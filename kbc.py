import streamlit as st
from PIL import Image
import os
import re
import random
from openai import OpenAI
from comfy import ComfyClient
import json
import io

# Set your OpenAI API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
comfy_client = ComfyClient("127.0.0.1:8188")

messages = []

# Path to save the image
SAVE_IMAGE_PATH = "E:\\new_ComfyUI_windows_portable_nvidia_cu121_or_cpu\\ComfyUI_windows_portable\\ComfyUI\\input\\"
WEBCAM_IMAGE_PATH = "E:\\new_ComfyUI_windows_portable_nvidia_cu121_or_cpu\\ComfyUI_windows_portable\\ComfyUI\\input\\"

# Helper functions
def send_message(role, content):
    messages.append({"role": role, "content": content})


def user_message(content):
    send_message('user', content)


def assistant_message(content):
    send_message('assistant', content)


def get_response(message=None):
    if message is not None:
        user_message(message)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )

    resp = response.choices[0].message.content.strip()

    assistant_message(resp)

    return resp


def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def save_webcam_image(image_data, filename="webcam_image.png"):
    """
    Save the webcam image to the specified directory and return the file path.
    """
    image = Image.open(image_data)
    save_path = os.path.join(SAVE_IMAGE_PATH, filename)
    image.save(save_path)
    return save_path


def create_book(prompt, style, age, art_style, webcam_image_path):
    main_character_name, main_character_description = create_main_character(prompt, style, age, art_style)
    st.write(f'Main Character: {main_character_name}')

    title = get_response('Give a title to the book. Your reply must be just the title formatted '
                         'in title case and nothing else. Do not label it. Do not describe it. '
                         'Just the title.')
    st.write(f'Title: {title}')
    sanitized_title = sanitize_filename(title)
    os.makedirs(sanitized_title, exist_ok=True)

    # Create main character illustration
    main_character_prompt, main_character_filename = create_main_element_illustration(
        title, main_character_name, main_character_description, age, art_style, webcam_image_path)

    main_elements, outline = get_book_outline(title, prompt, style, age)

    book_content = write_full_book(title, style, age, outline)

    pages = separate_pages(book_content, title)
    st.write(f"Number of pages: {len(pages)}")

    for page_num, page in enumerate(pages):
        page_text, illustration_notes = page
        # Save each page's text content to a file
        page_text_filename = os.path.join(sanitized_title, f'page_{page_num + 1}_text.txt')
        with open(page_text_filename, 'w') as f:
            f.write(page_text.strip())
        st.write(f'Saved text for page {page_num + 1} to {page_text_filename}')

        st.write(f"Creating illustration for page {page_num + 1}")
        messages.pop(1)
        create_illustration(title, f'page_{page_num + 1}_illustration',
                            page_text, main_character_name,
                            style, age, art_style, main_character_filename, main_character_prompt)

    output_log_path = os.path.join(sanitized_title, 'outputlog.txt')
    with open(output_log_path, 'w') as f:
        for m in messages:
            f.write(f'{m["role"]}:\n{m["content"]}\n\n')
    st.write('Output log saved to outputlog.txt')


def create_main_character(prompt, style, age, art_style):
    main_character_prompt = f"""
    Create the main character for our book.
    Here is a description of the book: {prompt}.
    Describe the main character in detail.
    """
    main_character_description = get_response(main_character_prompt)

    main_character_name = get_response("What is the name of the main character of the book? "
                                       "Respond with just the name and no other text at all.")

    return main_character_name, main_character_description


def get_book_outline(title, prompt, style, age):
    themes = [
        "Friendship", "Adventure", "Courage", "Kindness", "Family", "Acceptance",
        "Imagination", "Love", "Honesty", "Perseverance", "Curiosity", "Teamwork",
        "Responsibility", "Compassion", "Respect", "Bravery", "Creativity", "Sharing",
        "Learning", "Growth", "Nature", "Diversity", "Helping Others", "Overcoming Fears",
        "Discovery", "Joy", "Gratitude", "Patience", "Forgiveness", "Confidence",
        "Empathy", "Problem Solving", "Humor", "Determination", "Independence",
        "Self-Acceptance", "Loyalty", "Resilience", "Friendship with Animals", "Transformation",
        "Trust", "Generosity", "Environmental Awareness", "Cultural Understanding",
        "Conflict Resolution", "Mindfulness", "Adventure in Fantasy Worlds", "Overcoming Adversity",
        "History and Tradition", "Mysteries and Exploration", "Programming"
    ]

    selected_theme = random.choice(themes)
    book_outline_prompt = (
        f"I would like to write a children's book outline about {prompt}, themed around {selected_theme}, in the style of {style}, "
        f"for a child that is {age} years old. Create a detailed outline for a 20-page children's book. "
        f"Please create a book title and outline for the book. Some things to keep in mind before writing the outline:\n"
        f"1. Concept and Theme-\n"
        f" - Relevance: The concept of '{selected_theme}' should be relevant and age-appropriate for children.\n"
        f" - Educational Value: Many children's books aim to teach a lesson or moral. Consider what you want your readers to learn from '{selected_theme}'.\n"
        f"2. Storyline and Structure-\n"
        f" - Simplicity: The plot should be straightforward and easy for children to follow.\n"
        f" - Conflict and Resolution: Introduce a problem or challenge within the theme of '{selected_theme}' and lead the characters towards a resolution.\n"
        f"3. Characters-\n"
        f" - Relatability: Characters should be relatable and engaging for children. They often love characters that are slightly older than themselves but still relatable.\n"
        f" - Character Development: Even in short stories, characters should undergo some form of change or learning.\n"
        f"4. Language and Dialogue-\n"
        f" - Age-Appropriate Language: Use vocabulary and sentence structures suitable for the age group you are writing for.\n"
        f" - Read-Aloud Friendly: Many children's books are read aloud, so the language should flow well when spoken.\n"
        f"5. The absurd-\n"
        f" - Children love things portrayed absurdly, silly, whimsical. Taking things that often wouldn't go together and combining them.\n"
    )

    assistant_message_content = get_response(book_outline_prompt)
    sections = assistant_message_content.split('\n\n')

    main_elements_line = sections[-3]
    main_elements = main_elements_line.replace('Main Elements: ', '').split(', ')
    outline_text = '\n\n'.join(sections[1:]).strip()

    sanitized_title = sanitize_filename(title)
    os.makedirs(sanitized_title, exist_ok=True)

    with open(f"{sanitized_title}/{sanitized_title}_outline.txt", "w") as file:
        file.write(outline_text)

    return main_elements, outline_text


def write_full_book(title, style, age, outline):
    book_writing_prompt = (
        f"You are the most incredible and prolific children's author in the world. \n"
        f"Use the following outline and the style of {style} for a {age} year old child to write a children's book. \n"
        f"The book should be 20 pages long, you will provide the story and dialogue for each page and format it how it should be written on the page. \n"
        f"Each page should also include illustration notes describing what to draw.\n"
        f"Start with page 1 and end with page 20 making sure to separate the pages with page numbers. \n"
        f"It is vital to extract out certain things in the story to keep the illustrations consistent, every illustration note should be tagged with the initial prompt. \n"
        f"describe it as though you were explaining the scene to someone who cannot see. everything must be described in great detail. the action being performed and descriptions of \n"
        f"the objects in the scene are the main importance. \n"
        f"The outline for the story is: '{outline}'"
    )

    book_content = get_response(book_writing_prompt)
    st.write("Full Book Content:\n", book_content)
    return book_content


def separate_pages(book_content, title):
    page_pattern = re.compile(r'Page (\d+)(.*?)(?=Page \d+|$)', re.DOTALL)
    pages = page_pattern.findall(book_content)
    st.write(f"Separated {len(pages)} pages.")

    processed_pages = []
    for page_num, content in pages:
        parts = content.split('Illustration notes:')
        text = parts[0].strip()
        illustration_notes = parts[1].strip() if len(parts) > 1 else ""
        processed_pages.append((text, illustration_notes))

    return processed_pages


def create_main_element_illustration(title, character_name, character_description,
                                     age, art_style, webcam_image_path):
    # Full prompt with all the details and examples
    features = """
    Body Characteristics
    Body Type: Slim, athletic, curvy, muscular, etc.
    Height: Short, medium, tall.
    Posture: Straight, slouched, confident stance, etc.
    Clothing and Accessories
    Clothing Style: Casual, formal, sporty, etc.
    Clothing Colors: Specific colors or patterns worn.
    Accessories: Hats, scarves, watches, belts, etc."""

    gpt_prompt = (
        f"Create a prompt for stable diffusion. We want a vivid description that captures the essence of {character_name} of the book in"
        f"a terse manner for image creation."
        f"The book, titled '{title}', is designed for an audience of {age}-year-old children. "
        f"The illustration should reflect the style of '{art_style}'."
        f"Be succinct in describing every detail of characters, subjects, foreground, and background of the scene. "
        f"The illustration should be engaging and age-appropriate. "
        f"No text, letters, or numbers should be included in the image."
        f"Here is a description of the character: {character_description}."
        f"A character can be described via a list of attributes separated by commas: "
        f"{features}"
        f""
        f"Here are some example outputs. Follow these examples:"
        f""
        f"Example 1:"
        f"white 1girl, solo, in NYC, wideshot, small cute nose, eyelashes, eyeliner, hair covering one eye, twin braids hair, blue hair, freckles, excited, detailed yellow eyes, detailed face"
        f""
        f"Example 2:"
        f"white 1girl, solo, wideshot, riding a bike, small cute nose, eyelashes, eyeliner, hair covering one eye, twin braids hair, blue hair, freckles, excited, detailed yellow eyes, detailed face"
        f""
        f"Example 3:"
        f"1boy, solo, sitting, closed eyes, wideshot, white hair, outdoors, wings, sky, cloud, looking down, robot, mecha, science fiction, knee up, angel wings, white wings, android, very short hair, cyborg, mechanical wings, cyberpunk, retro"
        f""
        f"Example 4:"
        f"solo, 1male,  Viera, full body, wideshot (fluffy ears, fluff in ears:1.3), sitting on a throne, view from below, black top, long sleeves, orange skirt, checkered skirt, crossed legs, (sneakers:1.1), morning sun, beautifully backlit, a detailed painting, fantasy art, 1girl, freckles, round eyewear, pale skin, full lips, orange eyes, long hair, absurd res,"
        f""
        f"Make sure to include expression or emotion the character will have. format the prompt like the examples. do not write sentences. specify gender."
    )

    dalle_prompt = get_response(gpt_prompt)

    if len(dalle_prompt) > 100:
        dalle_prompt = get_response(f'Summarize this in less than 100 characters: {dalle_prompt}')

    with open('clip3_workflow_api.json', encoding='utf-8') as f:
        prompt = json.load(f)
    current_text = prompt["6"]["inputs"]["text"]
    updated_text = f"{current_text}, {dalle_prompt}"
    prompt["6"]["inputs"]["text"] = updated_text

    # Save webcam image into prompt to use in illustration creation
    prompt["41"]["inputs"]["image"] = webcam_image_path

    images = comfy_client.get_images(prompt)
    image_path = save_images(images, f"{sanitize_filename(title)}", sanitize_filename(character_name), ["41"])
    st.write(f"Illustration for {character_name} created: {image_path}")

    return dalle_prompt, image_path


def create_illustration(title, output_filename, page_content,
                        main_character_name, style, age,
                        art_style, main_character_filename,
                        main_character_prompt):
    examples = [
        "Example 1: full body image, A TV show poster for a parody series titled 'Breaking Bread,' playing on the name of the famous show Breaking Bad. The poster features a stern-looking baker in a flour-dusted apron, with a rolling pin slung over his shoulder like a weapon. He stands in the middle of a rustic bakery, surrounded by stacks of bread loaves, pastries, and bags of flour, all arranged to mimic the iconic desert backdrop from the original show. Behind him, the bakery's chalkboard menu lists items like 'Cinnamon Swirl Cartel' and 'Blueberry Muffin Meth,' hinting at the culinary chaos that’s about to unfold. The baker’s expression is intense, yet comically serious, as if he's about to take on the world with nothing but his dough and determination. The title 'Breaking Bread' is displayed in bold, stylized text at the top, with the 'Breaking' in a gritty, cracked font, while 'Bread' is written in warm, golden letters resembling freshly baked loaves. The tagline beneath reads, 'Baking is a Dangerous Game,' adding to the pun-filled humor. The overall color scheme of the poster is a mix of warm, bakery hues with the gritty, dark tones reminiscent of the original show, blending the intense drama of Breaking Bad with the lighthearted, culinary twist of 'Breaking Bread.'",
        "Example 2: a digital illustration of a movie poster titled 'Finding Emo', finding nemo parody poster, featuring a depressed cartoon clownfish with black emo hair, eyeliner, and piercings, bored expression, swimming in a dark underwater scene, in the background, movie title in a dripping, grungy font, moody blue and purple color palette",
        "Example 3: fullbody image, An old man sits serenely on a crescent moon, (fishing among the clouds:1.4). The scene has an evening, tranquil atmosphere. It’s dreamy and whimsical. deep depth of field, photography, Natural geographic photo, Hyper-realistic, 16k resolution, (masterpiece, award winning artwork), many details, extreme detailed, full of details, Wide range of colors, high Dynamic,",
        "Example 4: fullbody image, solo, 1male, Viera, full body, wideshot (fluffy ears, fluff in ears:1.3), sitting on a throne, view from below, black top, long sleeves, orange skirt, checkered skirt, crossed legs, (sneakers:1.1), morning sun, beautifully backlit, a detailed painting, fantasy art, 1girl, freckles, round eyewear, pale skin, full lips, orange eyes, long hair, absurd res"
    ]

    gpt_prompt = (
        f"You are a master at converting text into prompts for illustrations."
        f"\n\n"
        f"Decide the main focus and create a prompt that captures the essence of the following scene: '{page_content}'. "
        f"The main character is described as: {main_character_prompt}. "
        f"Analyze the sentence to identify the subject, predicate, direct object, indirect object, and subject complement. "
        f"If the main character '{main_character_name}' is the subject, include the following description of the character: {main_character_prompt}."
        f"The illustration should reflect the style of '{art_style}'. "
        f"Important elements that should be consistently depicted throughout the book include: {main_character_name}. "
        f"Be succinct in describing every detail of characters, subjects, foreground, and background of the scene.  "
        f"\n\n"
        f"Examples of prompts:"
        f"\n{examples[0]}"
        f"\n{examples[1]}"
        f"\n{examples[2]}"
        f"\n{examples[3]}"
        f"\n\n"
        f"Format the prompt like the examples but make sure to also describe the scene and environment. Begin the prompt with fullbody image and then a description of the scene. Specify gender."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": gpt_prompt}]
    )

    dalle_prompt = response.choices[0].message.content.strip()

    with open('faceswap4.json') as f:
        prompt = json.load(f)
    prompt["6"]["inputs"]["text"] = dalle_prompt
    prompt["41"]["inputs"]["image"] = main_character_filename

    images = comfy_client.get_images(prompt)
    output_path = save_images(images, f"{sanitize_filename(title)}", output_filename)

    st.write(f"Illustration created and saved to: {output_path}")
    return output_path


def save_images(images, save_dir, filename_prefix='', node=None):
    saved_paths = []

    os.makedirs(save_dir, exist_ok=True)

    for node_id in images:
        for i, image_data in enumerate(images[node_id]):
            image = Image.open(io.BytesIO(image_data))
            save_path = os.path.join(save_dir, f"{filename_prefix}_{node_id}_{i}.png")
            image.save(save_path)
            st.write(f"Saved image to: {save_path}")
            saved_paths.append(save_path)

    if saved_paths:
        return saved_paths[0]
    return None


# Streamlit App
st.title("Create Your Children's Book")

# Step 1: Capture webcam image
picture = st.camera_input("Take a picture for your book creation")

webcam_image_path = None
if picture:
    # Save the image to a file in the specified directory
    webcam_image_path = save_webcam_image(picture)

    st.image(picture, caption="Captured Image", use_column_width=True)

# Step 2: Collect inputs
book_prompt = st.text_input("Enter a prompt for the book's theme or story")
style = st.text_input("Enter the style of the book (e.g., Dr. Seuss)")
art_style = st.text_input("Enter the art style of the book (e.g., 3D animation, watercolor)")
age = st.number_input("Enter the target age group for the book", min_value=1, max_value=100, step=1)

if st.button("Create Book"):
    if not book_prompt or not style or not art_style or not age or not webcam_image_path:
        st.warning("Please fill out all fields and take a webcam picture.")
    else:
        create_book(book_prompt, style, age, art_style, webcam_image_path)

