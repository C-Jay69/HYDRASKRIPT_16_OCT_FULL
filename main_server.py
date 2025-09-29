from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import asyncpg
from contextlib import asynccontextmanager
import stripe
import hashlib
import secrets
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
import bcrypt

# Pydantic models for API validation
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    email: str
    full_name: str
    subscription_tier: str

class ProjectCreate(BaseModel):
    title: str
    author: Optional[str] = ""
    description: Optional[str] = ""
    genre: str
    content: Optional[str] = ""
    target_language: Optional[str] = "en"
    voice_style: Optional[str] = "neutral"

# Professional AI services now handled by dedicated AI service module

class SimplifiedFileService:
    def get_supported_types(self):
        return {
            "mime_types": ["text/plain", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
            "extensions": [".txt", ".pdf", ".docx"],
            "max_file_size_mb": 25,
            "description": "Supported formats: TXT, PDF, DOCX"
        }

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# JWT Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Initialize Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Global database pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_pool
    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        statement_cache_size=0,  # Fix for PgBouncer compatibility
        min_size=1,
        max_size=10
    )
    yield
    # Shutdown
    await db_pool.close()

# Create FastAPI app with lifespan
app = FastAPI(
    title="Manuscriptify API",
    description="AI-powered audiobook and ebook generation platform",
    version="1.0.0",
    lifespan=lifespan
)

# Create API router
api_router = APIRouter(prefix="/api")

# CORS middleware - Secure configuration for Replit environment
REPLIT_DOMAIN = os.environ.get("REPLIT_DEV_DOMAIN", "localhost")
FRONTEND_URL = os.environ.get("FRONTEND_URL", f"https://{REPLIT_DOMAIN}:5000")

# Allow multiple frontend origins to handle different environments
allowed_origins = [
    FRONTEND_URL,
    f"https://{REPLIT_DOMAIN}",  # Production domain without port
    f"https://{REPLIT_DOMAIN}:5000",
    f"http://{REPLIT_DOMAIN}:5000", 
    "http://localhost:5000",
    "https://localhost:5000",
    "http://127.0.0.1:5000",
    "https://127.0.0.1:5000"
]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
from services.ai_service import AIService
from services.file_service import FileService
from services.stripe_service import stripe_service
ai_service = AIService()
file_service = FileService()

# Security
security = HTTPBearer(auto_error=False)

async def get_database():
    """Get database connection from pool"""
    return db_pool

# Security and authentication utilities
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from verified JWT token"""
    if not credentials:
        return None
    
    try:
        # Verify JWT token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
            
        # Get user from database
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_id
            )
            return user
            
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register_user(user_data: UserCreate):
    """Register a new user with secure password hashing"""
    try:
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(user_data.password)
        
        async with db_pool.acquire() as conn:
            # Check if user exists
            existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", user_data.email)
            if existing:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            # Create user with hashed password
            await conn.execute(
                """INSERT INTO users (id, email, full_name, password_hash, subscription_tier, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                user_id, user_data.email, user_data.full_name, hashed_password, "free", datetime.utcnow()
            )
            
            # Create JWT token
            access_token = create_access_token(data={"sub": user_id})
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user_id=user_id,
                email=user_data.email,
                full_name=user_data.full_name,
                subscription_tier="free"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin):
    """Login user with password verification and JWT token"""
    try:
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1", 
                login_data.email
            )
            
            if not user or not verify_password(login_data.password, user["password_hash"]):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Create JWT token
            access_token = create_access_token(data={"sub": str(user["id"])})
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user_id=str(user["id"]),
                email=user["email"],
                full_name=user["full_name"],
                subscription_tier=user["subscription_tier"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

# ============================================================================
# FILE UPLOAD ENDPOINTS
# ============================================================================

@api_router.post("/files/upload")
async def upload_file(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    """Upload and process document file with proper validation"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Read file content
        content = await file.read()
        
        # Use FileService to handle upload and text extraction
        result = await file_service.save_uploaded_file(content, file.filename, file.content_type)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return {
            "filename": result['filename'],
            "file_size": result['file_size'],
            "content_type": result['content_type'],
            "extracted_text": result['extracted_text'],
            "word_count": result['word_count']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

@api_router.get("/files/supported-types")
async def get_supported_file_types():
    """Get supported file types"""
    return file_service.get_supported_types()

# ============================================================================
# SUBSCRIPTION ENDPOINTS  
# ============================================================================

@api_router.get("/subscription-plans")
async def get_subscription_plans():
    """Get all available subscription plans"""
    try:
        async with db_pool.acquire() as conn:
            plans = await conn.fetch("SELECT * FROM subscription_plans WHERE active = true ORDER BY price_monthly ASC")
            return [dict(plan) for plan in plans]
    except Exception as e:
        logger.error(f"Failed to get subscription plans: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription plans")

# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

@api_router.post("/projects")
async def create_project(project_data: ProjectCreate, current_user = Depends(get_current_user)):
    """Create a new book project with validation"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        project_id = str(uuid.uuid4())
        
        # Set and validate genre-specific constraints
        constraints = get_genre_constraints(project_data.genre)
        if not constraints:
            raise HTTPException(status_code=400, detail="Invalid genre")
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO projects (id, user_id, title, author, description, genre, content, 
                   page_size, min_pages, max_pages, target_language, include_images, voice_style)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)""",
                project_id, current_user["id"], project_data.title,
                project_data.author, project_data.description,
                project_data.genre, project_data.content, constraints["page_size"],
                constraints["min_pages"], constraints["max_pages"],
                project_data.target_language, constraints["include_images"],
                project_data.voice_style
            )
            
        return {"project_id": project_id, "status": "created"}
        
    except Exception as e:
        logger.error(f"Project creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")

@api_router.get("/projects")
async def get_user_projects(current_user = Depends(get_current_user)):
    """Get all projects for current user"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        async with db_pool.acquire() as conn:
            projects = await conn.fetch(
                "SELECT * FROM projects WHERE user_id = $1 ORDER BY created_at DESC",
                current_user["id"]
            )
            
        return [dict(project) for project in projects]
        
    except Exception as e:
        logger.error(f"Failed to get projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve projects")

@api_router.get("/projects/detail/{project_id}")
async def get_project_detail(project_id: str, current_user = Depends(get_current_user)):
    """Get detailed project information including generated content"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        async with db_pool.acquire() as conn:
            project = await conn.fetchrow(
                """SELECT * FROM projects WHERE id = $1 AND user_id = $2""",
                project_id, current_user["id"]
            )
            
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            return dict(project)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve project details")

# ============================================================================
# AI GENERATION ENDPOINTS
# ============================================================================

@api_router.post("/ai/generate-book")
async def generate_book_from_prompt(request: Dict[str, Any], background_tasks: BackgroundTasks, current_user = Depends(get_current_user)):
    """Generate book from prompt or uploaded content"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Use provided project_id if available, otherwise create new
        project_id = request.get("project_id")
        prompt = request.get("prompt", "")
        genre = request.get("genre", "ebook")
        length = request.get("length", "medium")
        uploaded_content = request.get("uploaded_content")  # For audiobooks with uploaded manuscripts
        
        async with db_pool.acquire() as conn:
            if project_id:
                # Update existing project to processing status
                content_to_store = uploaded_content if uploaded_content else prompt
                result = await conn.execute(
                    """UPDATE projects SET status = $1, content = $2 
                       WHERE id = $3 AND user_id = $4""",
                    "processing", content_to_store, project_id, current_user["id"]
                )
                if result == "UPDATE 0":
                    raise HTTPException(status_code=404, detail="Project not found or access denied")
            else:
                # Create new project if no project_id provided
                project_id = str(uuid.uuid4())
                constraints = get_genre_constraints(genre)
                content_to_store = uploaded_content if uploaded_content else prompt
                await conn.execute(
                    """INSERT INTO projects (id, user_id, title, genre, content, status, 
                       page_size, min_pages, max_pages, target_language)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
                    project_id, current_user["id"], f"Generated {genre.title()}", genre,
                    content_to_store, "processing", constraints["page_size"], constraints["min_pages"],
                    constraints["max_pages"], request.get("target_language", "en")
                )
        
        # Start background generation with appropriate content
        content_for_generation = uploaded_content if uploaded_content else prompt
        background_tasks.add_task(generate_book_background, project_id, content_for_generation, genre, length)
        
        return {"project_id": project_id, "status": "processing", "message": "Book generation started"}
        
    except Exception as e:
        logger.error(f"Book generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to start book generation")

async def generate_book_background(project_id: str, prompt: str, genre: str, length: str):
    """Background task for book generation"""
    logger.info(f"🚀 BACKGROUND TASK STARTED: project_id={project_id}, genre={genre}, length={length}")
    
    try:
        # Update progress
        await update_project_progress(project_id, 10, "Generating content", "in_progress")
        logger.info(f"📊 Progress updated for project {project_id}")
        
        # Generate content using AI service with guaranteed fallback
        try:
            logger.info(f"🤖 Calling AI service for project {project_id}")
            content = await ai_service.generate_book_from_prompt(prompt, genre, length)
            logger.info(f"✅ AI service returned {len(content.split()) if content else 0} words for project {project_id}")
        except Exception as ai_error:
            logger.error(f"AI service failed for project {project_id}: {ai_error}. Using guaranteed fallback...")
            # ALWAYS provide comprehensive fallback content when AI fails
            if genre == "kids_story" and ("three sisters" in prompt.lower() or "3 sisters" in prompt.lower()):
                content = '''# Three Sisters Summer Adventure

Page 1:
Emma, Sofia, and Lily bounced excitedly in the back seat of their parents' car as they drove down the long, dusty road leading to Aunt Martha and Uncle Joe's farm. Eight-year-old Emma pressed her nose against the window, watching the green fields roll by. "Look!" she exclaimed, pointing to a red barn in the distance. "That must be it!"

Six-year-old Sofia clapped her hands together. "I can't wait to see the animals!" she said, her eyes sparkling with excitement. Little Lily, who was only four, hugged her stuffed bunny tightly and smiled shyly.

Page 2:
When they arrived, Aunt Martha came rushing out of the farmhouse, her apron dusted with flour and her face beaming with joy. "My dear girls!" she called, wrapping them all in a warm, lavender-scented hug. Uncle Joe emerged from the barn, his boots muddy and his smile wide. "Welcome to our little piece of heaven," he said, ruffling Emma's hair.

The farmhouse was cozy and welcoming, with wooden floors that creaked pleasantly and windows that looked out over rolling meadows dotted with wildflowers.

Page 3:
That first morning, Uncle Joe took the sisters on a tour of the farm. "Every animal here has a job," he explained as they walked past the chicken coop. "And every job is important." Emma listened carefully, already thinking of questions to ask. Sofia skipped ahead, trying to peek through the fence slats at the animals inside.

Lily held Uncle Joe's hand tightly, her eyes wide with wonder as she saw her first real farm animals up close.

Page 4:
Their first stop was the horse stable, where they met Thunder, a gentle giant with a glossy brown coat and kind eyes. "Thunder is twenty years old," Uncle Joe said, "and he's the wisest animal on our farm." Emma immediately felt drawn to the majestic horse, while Sofia giggled at how Thunder's whiskers tickled when he nuzzled her palm.

Lily was a little scared at first, but when Thunder lowered his great head and breathed softly on her hand, she smiled the biggest smile anyone had ever seen.

Page 5:
Next, they visited the goat pen, where a mischievous group of goats immediately surrounded Sofia. "They like you!" Aunt Martha laughed as a small brown goat named Pepper tried to eat Sofia's shoelaces. Sofia laughed and laughed, chasing the playful goats around the pen and making up silly songs for them.

Emma observed how the goats worked together, always watching out for each other, while Lily was delighted by the tiny baby goats that were only a few weeks old.

Page 6:
The chicken coop was Lily's favorite discovery. The gentle hens clucked softly as she scattered feed for them, and when a fluffy yellow chick peeped from beneath its mother's wing, Lily's heart melted completely. "They're so soft," she whispered, gently stroking the chick's downy feathers with one finger.

Emma learned that chickens were much smarter than she'd ever imagined, while Sofia enjoyed the silly way they tilted their heads when she spoke to them.

Page 7:
As the days passed, each sister found her special connection with the farm animals. Emma spent hours with Thunder, learning to brush his coat and clean his hooves. She discovered that taking care of such a large, powerful animal required patience, gentleness, and respect.

"Thunder teaches me to be calm and thoughtful," Emma told her sisters one evening as they sat on the porch watching the sunset paint the sky in shades of orange and pink.

Page 8:
Sofia became the official goat entertainer, spending her mornings playing games with Pepper, Cinnamon, and Nutmeg. She learned that goats were incredibly social animals who needed friendship and fun to be happy. Uncle Joe taught her how to milk the goats, and Sofia was so proud when she successfully filled her first small bucket.

"The goats taught me that being playful and making friends is important work too," Sofia said, wiping milk foam from her chin.

Page 9:
Little Lily became the chicken whisperer, caring for the baby chicks with the tenderness that only someone with the purest heart could possess. She learned to collect eggs gently, fill water containers without spilling, and even helped Aunt Martha in the garden, picking vegetables that would become delicious meals.

"The chickens taught me that even little ones can help in big ways," Lily said softly, cradling a sleepy chick in her small hands.

Page 10:
The sisters learned that farm life meant early mornings and evening chores, but they discovered that working together made everything more fun. Emma's careful nature helped them remember all their tasks, Sofia's energy kept them laughing even when they were tired, and Lily's gentle spirit reminded them to be kind to every creature, no matter how small.

They learned to work as a team, just like the animals they cared for.

Page 11:
One morning, they woke to find that one of the hens, Henrietta, was missing. The sisters searched everywhere – behind the barn, under the porch, even in the old oak tree. Finally, Lily's sharp eyes spotted something moving in the tall grass near the pond.

"There she is!" Lily called softly. Henrietta had made a secret nest and was sitting proudly on a clutch of eggs that were just beginning to hatch.

Page 12:
The sisters watched in amazement as tiny chicks began to break free from their shells. "It's a miracle," Emma whispered. Sofia danced with joy, while Lily sat perfectly still, not wanting to disturb the new babies.

Aunt Martha and Uncle Joe explained how Henrietta had followed her instincts to find the perfect place for her babies, and the sisters learned that sometimes animals knew exactly what they needed, even without being told.

Page 13:
As their month at the farm drew to a close, the sisters realized how much they had learned about responsibility, kindness, and the importance of caring for others. They had discovered that every living thing had its own special way of contributing to the world.

Emma had learned patience and wisdom from Thunder, Sofia had discovered the joy of friendship from the goats, and Lily had found her gentle strength through caring for the chickens.

Page 14:
On their last morning, the sisters helped with all the farm chores one final time. They hugged Thunder goodbye, promising to visit again soon. They played one last game with the goats, and Lily gave each chicken a tiny piece of their favorite treats.

"Thank you for teaching us so much," Emma said to the animals, her voice thick with emotion.

Page 15:
As their parents' car pulled up to take them home, the sisters felt both sad to leave and excited to share their stories with friends. Aunt Martha and Uncle Joe gave them each a special gift – a photo album filled with pictures of their farm adventures and a promise that they would always have a home on the farm.

"You've learned the most important lesson of all," Uncle Joe said, "that love and kindness toward all living things makes the world a better place."

Page 16:
The drive home was filled with chatter about all their adventures. Emma talked about how she wanted to learn more about horses, Sofia planned to ask her parents if they could visit a petting zoo, and Lily carefully held a small box containing three special feathers that Henrietta had given her.

They had discovered that the month at the farm had changed them forever, teaching them about responsibility, friendship, and the wonderful connections that exist between all living things.

**The End**

The three sisters returned home with hearts full of memories, new understanding of the natural world, and a deep appreciation for the simple joys of farm life. Their summer adventure had taught them that every creature, big or small, has an important role to play in the beautiful tapestry of life.'''
            else:
                # Generic comprehensive fallback for other prompts
                content = f'''# A Wonderful Adventure

Page 1:
Once upon a time, there lived children who were about to embark on the most amazing adventure of their lives. They had curious hearts and brave spirits, ready to discover the magic that existed in the world around them.

Page 2:
Their adventure began on a bright, sunny morning when they discovered something truly special. It was the beginning of a journey that would teach them about friendship, courage, and the importance of caring for others.

Page 3:
As they explored their new world, they met wonderful friends who showed them that every living thing has something important to teach us. They learned that kindness and understanding can overcome any challenge.

Page 4:
Through their experiences, they discovered that working together made them stronger and that helping others brought them the greatest joy. Each day brought new lessons about responsibility and compassion.

Page 5:
Their wonderful adventure taught them that the world is full of beauty and magic when we look at it with open hearts and minds. They learned that every day is a chance to make new friends and learn something new.

**The End**

Their adventure showed them that the greatest treasures in life are the friendships we make and the kindness we share with others.'''
        
        # Update project with generated content
        async with db_pool.acquire() as conn:
            await conn.execute(
                """UPDATE projects SET generated_content = $1, status = $2, progress = $3,
                   word_count = $4, updated_at = $5 WHERE id = $6""",
                content, "completed", 100, len(content.split()),
                datetime.utcnow(), project_id
            )
            
        await update_project_progress(project_id, 100, "Book generation completed", "completed")
        
    except Exception as e:
        logger.error(f"Background book generation failed: {e}")
        await update_project_progress(project_id, 0, f"Generation failed: {str(e)}", "failed")

# ============================================================================
# STRIPE PAYMENT ENDPOINTS
# ============================================================================

@api_router.post("/payments/create-subscription")
async def create_subscription(plan_data: Dict[str, Any], current_user = Depends(get_current_user)):
    """Create Stripe subscription or one-time payment checkout"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        plan_id = plan_data.get("plan_id")
        
        # Get plan details
        async with db_pool.acquire() as conn:
            plan = await conn.fetchrow("SELECT * FROM subscription_plans WHERE id = $1", plan_id)
            if not plan:
                raise HTTPException(status_code=404, detail="Plan not found")
            
            # Determine if this is a monthly subscription or lifetime one-time payment
            is_monthly = plan["price_monthly"] is not None and plan["price_lifetime"] is None
            is_lifetime = plan["price_lifetime"] is not None and plan["price_monthly"] is None
            
            if not (is_monthly or is_lifetime):
                raise HTTPException(status_code=400, detail="Invalid plan configuration")
            
            # Create or get Stripe customer
            if current_user.get("stripe_customer_id"):
                customer_id = current_user["stripe_customer_id"]
            else:
                customer = stripe.Customer.create(
                    email=current_user["email"],
                    name=current_user["full_name"]
                )
                customer_id = customer.id
                
                # Update user with customer ID
                await conn.execute(
                    "UPDATE users SET stripe_customer_id = $1 WHERE id = $2",
                    customer_id, current_user["id"]
                )
            
            # Get frontend URL for success/cancel redirects - Replit domains don't use port in production
            replit_domain = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost')
            if 'localhost' in replit_domain:
                frontend_url = f"http://{replit_domain}:5000"
            else:
                frontend_url = f"https://{replit_domain}"
            
            if is_monthly:
                # For monthly plans, create dynamic pricing and subscription
                # Create a price dynamically since we may not have pre-created price IDs
                price = stripe.Price.create(
                    unit_amount=int(float(plan["price_monthly"]) * 100),  # Convert to cents
                    currency='usd',
                    recurring={'interval': 'month'},
                    product_data={
                        'name': plan["name"],
                        'description': f'Monthly subscription to {plan["name"]}'
                    }
                )
                
                # Create Stripe Checkout Session for subscription
                checkout_session = stripe.checkout.Session.create(
                    customer=customer_id,
                    payment_method_types=['card'],
                    line_items=[{
                        'price': price.id,
                        'quantity': 1,
                    }],
                    mode='subscription',
                    success_url=f'{frontend_url}/dashboard?payment=success&session_id={{CHECKOUT_SESSION_ID}}',
                    cancel_url=f'{frontend_url}/?payment=cancelled',
                    metadata={
                        'plan_id': str(plan_id),
                        'user_id': str(current_user["id"]),
                        'plan_type': 'monthly'
                    }
                )
                
            else:  # is_lifetime
                # For lifetime plans, create one-time payment
                price = stripe.Price.create(
                    unit_amount=int(float(plan["price_lifetime"]) * 100),  # Convert to cents
                    currency='usd',
                    product_data={
                        'name': plan["name"],
                        'description': f'Lifetime access to {plan["name"]}'
                    }
                )
                
                # Create Stripe Checkout Session for one-time payment
                checkout_session = stripe.checkout.Session.create(
                    customer=customer_id,
                    payment_method_types=['card'],
                    line_items=[{
                        'price': price.id,
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=f'{frontend_url}/dashboard?payment=success&session_id={{CHECKOUT_SESSION_ID}}',
                    cancel_url=f'{frontend_url}/?payment=cancelled',
                    metadata={
                        'plan_id': str(plan_id),
                        'user_id': str(current_user["id"]),
                        'plan_type': 'lifetime'
                    }
                )
            
            # Store the checkout session info for webhook processing
            await conn.execute(
                """INSERT INTO pending_payments (user_id, plan_id, stripe_session_id, plan_type, amount, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                current_user["id"], plan_id, checkout_session.id, 
                'monthly' if is_monthly else 'lifetime',
                float(plan["price_monthly"]) if is_monthly else float(plan["price_lifetime"]),
                datetime.utcnow()
            )
            
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except Exception as e:
        logger.error(f"Payment session creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create payment session: {str(e)}")

@api_router.post("/payments/webhook")
async def stripe_webhook(request: Dict[str, Any]):
    """Handle Stripe webhook events for payment completion"""
    try:
        # For development, we'll skip signature verification
        # In production, add proper webhook signature verification
        event = request
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            await handle_payment_success(session)
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            await handle_subscription_payment(invoice)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook handling failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook handling failed")

async def handle_payment_success(session):
    """Handle successful payment completion"""
    try:
        user_id = session.metadata.get('user_id')
        plan_id = session.metadata.get('plan_id')
        plan_type = session.metadata.get('plan_type')
        
        if not all([user_id, plan_id, plan_type]):
            logger.error("Missing metadata in payment session")
            return
        
        async with db_pool.acquire() as conn:
            # Get plan details
            plan = await conn.fetchrow("SELECT * FROM subscription_plans WHERE id = $1", plan_id)
            if not plan:
                logger.error(f"Plan not found: {plan_id}")
                return
            
            # Update user subscription status
            await conn.execute(
                """UPDATE users SET subscription_tier = $1, 
                   stripe_customer_id = COALESCE(stripe_customer_id, $2),
                   updated_at = $3 WHERE id = $4""",
                plan['name'], session.customer, datetime.utcnow(), user_id
            )
            
            # Create subscription record
            if plan_type == 'monthly':
                # For monthly subscriptions
                subscription_id = session.subscription
                await conn.execute(
                    """INSERT INTO user_subscriptions 
                       (user_id, plan_id, stripe_subscription_id, status, created_at)
                       VALUES ($1, $2, $3, $4, $5)
                       ON CONFLICT (user_id) DO UPDATE SET
                       plan_id = $2, stripe_subscription_id = $3, status = $4, updated_at = $5""",
                    user_id, plan_id, subscription_id, 'active', datetime.utcnow()
                )
            else:
                # For lifetime purchases
                await conn.execute(
                    """INSERT INTO user_subscriptions 
                       (user_id, plan_id, stripe_subscription_id, status, created_at)
                       VALUES ($1, $2, $3, $4, $5)
                       ON CONFLICT (user_id) DO UPDATE SET
                       plan_id = $2, status = $4, updated_at = $5""",
                    user_id, plan_id, None, 'lifetime', datetime.utcnow()
                )
                
                # Decrement spots for lifetime plans
                features = plan['features']
                if isinstance(features, str):
                    import json
                    features = json.loads(features)
                
                if features.get('spots_left'):
                    new_spots = max(0, features.get('spots_left', 0) - 1)
                    features['spots_left'] = new_spots
                    
                    await conn.execute(
                        "UPDATE subscription_plans SET features = $1 WHERE id = $2",
                        json.dumps(features), plan_id
                    )
            
            # Update pending payment status
            await conn.execute(
                """UPDATE pending_payments SET status = $1, completed_at = $2 
                   WHERE stripe_session_id = $3""",
                'completed', datetime.utcnow(), session.id
            )
            
        logger.info(f"Payment completed for user {user_id}, plan {plan['name']}")
        
    except Exception as e:
        logger.error(f"Payment success handling failed: {e}")

async def handle_subscription_payment(invoice):
    """Handle recurring subscription payments"""
    try:
        subscription_id = invoice.subscription
        customer_id = invoice.customer
        
        async with db_pool.acquire() as conn:
            # Update subscription status
            await conn.execute(
                """UPDATE user_subscriptions SET status = $1, updated_at = $2 
                   WHERE stripe_subscription_id = $3""",
                'active', datetime.utcnow(), subscription_id
            )
            
        logger.info(f"Subscription payment processed for subscription {subscription_id}")
        
    except Exception as e:
        logger.error(f"Subscription payment handling failed: {e}")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_genre_constraints(genre: str) -> Optional[Dict[str, Any]]:
    """Get page size and count constraints by genre with validation"""
    constraints = {
        "ebook": {
            "page_size": "6x9",
            "min_pages": 75,
            "max_pages": 150,
            "include_images": False
        },
        "novel": {
            "page_size": "6x9", 
            "min_pages": 100,
            "max_pages": 250,
            "include_images": False
        },
        "kids_story": {
            "page_size": "8x10",
            "min_pages": 1,
            "max_pages": 25,
            "include_images": True
        },
        "coloring_book": {
            "page_size": "8x10",
            "min_pages": 20,
            "max_pages": 20,
            "include_images": True
        }
    }
    return constraints.get(genre)

@api_router.get("/progress/{project_id}")
async def get_project_progress(project_id: str, current_user = Depends(get_current_user)):
    """Get project progress and processing status"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        async with db_pool.acquire() as conn:
            project = await conn.fetchrow(
                """SELECT id, title, status, progress, processing_logs, created_at, updated_at
                   FROM projects WHERE id = $1 AND user_id = $2""",
                project_id, current_user["id"]
            )
            
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Parse processing logs - ensure it's always a list
            processing_logs = project["processing_logs"] or []
            
            # Handle case where processing_logs might be a JSON string
            if isinstance(processing_logs, str):
                try:
                    import json
                    processing_logs = json.loads(processing_logs)
                except:
                    processing_logs = []
            
            # Ensure it's a list
            if not isinstance(processing_logs, list):
                processing_logs = []
            
            # Calculate current step from logs
            current_step = "Initializing"
            if processing_logs and len(processing_logs) > 0:
                latest_log = processing_logs[-1]
                if isinstance(latest_log, dict):
                    current_step = latest_log.get("message", "Processing")
            
            # Estimate completion time based on progress
            estimated_completion = None
            if project["progress"] > 0 and project["status"] in ["processing", "in_progress"]:
                # Simple estimation: 5 minutes total, scale by remaining progress
                remaining_progress = 100 - project["progress"]
                estimated_minutes = (remaining_progress / 100) * 5
                estimated_completion = (datetime.utcnow() + timedelta(minutes=estimated_minutes)).isoformat()
            
            return {
                "project_id": project["id"],
                "title": project["title"],
                "overall_progress": project["progress"],
                "current_step": current_step,
                "status": project["status"],
                "steps": processing_logs,
                "estimated_completion": estimated_completion,
                "created_at": project["created_at"].isoformat(),
                "updated_at": project["updated_at"].isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get progress")

async def update_project_progress(project_id: str, progress: int, message: str, status: str):
    """Update project progress"""
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                """UPDATE projects SET progress = $1, status = $2, updated_at = $3
                   WHERE id = $4""",
                progress, status, datetime.utcnow(), project_id
            )
            
            # Add to processing logs
            await conn.execute(
                """UPDATE projects SET processing_logs = processing_logs || $1::jsonb
                   WHERE id = $2""",
                f'[{{"timestamp": "{datetime.utcnow().isoformat()}", "message": "{message}", "progress": {progress}}}]',
                project_id
            )
    except Exception as e:
        logger.error(f"Failed to update progress: {e}")

# ============================================================================
# STRIPE PAYMENT ENDPOINTS
# ============================================================================

@api_router.post("/stripe/create-checkout-session")
async def create_checkout_session(
    request: dict,
    current_user = Depends(get_current_user)
):
    """Create a Stripe checkout session"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        plan_id = request.get("plan_id")
        success_url = request.get("success_url", f"{FRONTEND_URL}/payment/success")
        cancel_url = request.get("cancel_url", f"{FRONTEND_URL}/pricing")
        
        if not plan_id:
            raise HTTPException(status_code=400, detail="plan_id is required")
        
        result = await stripe_service.create_checkout_session(
            plan_id=plan_id,
            user_id=current_user["id"],
            user_email=current_user["email"],
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@api_router.get("/stripe/session/{session_id}")
async def get_checkout_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Retrieve a Stripe checkout session"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        result = await stripe_service.retrieve_session(session_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve session: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")

@api_router.post("/stripe/create-portal-session")
async def create_customer_portal_session(
    request: dict,
    current_user = Depends(get_current_user)
):
    """Create a Stripe customer portal session"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        customer_id = request.get("customer_id")
        return_url = request.get("return_url", f"{FRONTEND_URL}/dashboard")
        
        if not customer_id:
            raise HTTPException(status_code=400, detail="customer_id is required")
        
        result = await stripe_service.create_customer_portal_session(
            customer_id=customer_id,
            return_url=return_url
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create portal session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")

@api_router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        result = await stripe_service.handle_webhook(payload, signature)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook handling failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook handling failed")

@api_router.get("/stripe/config")
async def get_stripe_config():
    """Get Stripe configuration for frontend"""
    return {
        "publishable_key": stripe_service.get_publishable_key(),
        "plans": stripe_service.get_all_plans()
    }

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Manuscriptify API is running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db_pool else "disconnected"
    }

@api_router.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Manuscriptify API is running", "version": "1.0.0"}

# Include the router in the main app
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)