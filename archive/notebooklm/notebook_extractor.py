import asyncio
import argparse
import json
from playwright.async_api import async_playwright
import os
import re

async def extract_from_pdf(pdf_path, output_path):
    print(f"Starting extraction for {pdf_path}...")
    abs_pdf_path = os.path.abspath(pdf_path)
    
    if not os.path.exists(abs_pdf_path):
        print(f"Error: File {abs_pdf_path} does not exist.")
        return

    async with async_playwright() as p:
        # Load the saved session in headless mode
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./notebooklm_profile",
            executable_path='/usr/bin/brave-browser',
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("Navigating to NotebookLM...")
        await page.goto("https://notebooklm.google.com/")
        
        # Wait for the dashboard to load (look for 'New Notebook' or similar)
        try:
            # The 'New Notebook' button usually has specific text or aria labels.
            # We'll use a broad text selector and wait.
            print("Looking for 'New Notebook' button...")
            await page.wait_for_selector("text=New Notebook", timeout=15000)
            await page.click("text=New Notebook")
            print("Created a new notebook.")
        except Exception as e:
            print("Could not find 'New Notebook' button. Are you logged in? Error:", e)
            await context.close()

            return
            
        await page.wait_for_timeout(3000)
        
        try:
            print(f"Uploading PDF file: {pdf_path}...")
            async with page.expect_file_chooser() as fc_info:
                await page.locator("text=Upload files").click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(pdf_path)
        except Exception as e:
            print("Failed to upload file. The UI might have changed:", e)
            await context.close()
            return
            
        # Processing might take 20-40 seconds for large PDFs. 
        # We must wait for the source count to update to '1 source' or '1 sources'
        print("Waiting for document upload to finish...")
        try:
            await page.wait_for_selector("text=/1 source/", timeout=60000)
            
            print("Document added. Waiting 15 seconds for NotebookLM backend to ingest it before chatting...")
            await page.wait_for_timeout(15000)
            
            chat_input = page.get_by_placeholder("Start typing...")
            await chat_input.wait_for(state="visible")
        except Exception as e:
            print("Timeout waiting for document processing:", e)
            await context.close()
            return
            
        print("Sending extraction prompt...")
        
        prompt = """
    Please read the attached earnings concall transcript. 
    Provide a full and highly detailed summary of the FIRST major discussion or the opening remarks of the concall. 
    Focus on capturing all the important points and nuances mentioned by the management.
    """
        
        await chat_input.fill(prompt)
        await page.keyboard.press("Enter")
        
        print("Waiting for AI response (30 seconds)...")
        # Give NotebookLM some time to stream the response
        await page.wait_for_timeout(30000) 
        
        print("Scraping response...")
        # NotebookLM chats usually appear in role-based blocks
        response_text = await page.evaluate("""() => {
            return document.body.innerText;
        }""")
        
        # Save the full text response instead of trying to parse JSON
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response_text)
            
        print(f"\n✅ Extraction complete! Response saved to {output_path}")
            
        await context.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract Summary from PDF using NotebookLM")
    parser.add_argument("--input", required=True, help="Path to input PDF file")
    parser.add_argument("--output", required=True, help="Path to save output text/markdown file")
    
    args = parser.parse_args()
    asyncio.run(extract_from_pdf(args.input, args.output))
