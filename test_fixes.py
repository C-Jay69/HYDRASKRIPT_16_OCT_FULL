import asyncio
from backend.services.ai_service import AIService

async def main():
    ai = AIService()

    # Test image generation
    story_text = """Page 1: The quick brown fox jumps over the lazy dog.
    Page 2: The lazy dog sleeps under the warm sun."""
    story_theme = "A story about a fox and a dog"
    illustrated_book = await ai.generate_book_with_images(story_text, story_theme)
    print("--- Image Generation Test ---")
    if illustrated_book and illustrated_book['illustrated_pages']:
        for page in illustrated_book['illustrated_pages']:
            print(f"Page {page['page_number']}: {page['image_specification']}")
    else:
        print("Image generation failed.")

    # Test text generation
    prompt = "Write a short story about a brave knight."
    genre = "kids_story"
    story = await ai.generate_book_from_prompt(prompt, genre)
    print("\n--- Text Generation Test ---")
    if story and "Page 1" in story:
        print("Story generated successfully.")
        print(story[:500] + "...")
    else:
        print("Story generation failed.")

if __name__ == "__main__":
    asyncio.run(main())


