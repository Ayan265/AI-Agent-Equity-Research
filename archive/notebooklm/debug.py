import asyncio
from playwright.async_api import async_playwright

async def debug_upload():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./notebooklm_profile",
            executable_path='/usr/bin/brave-browser',
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        await page.goto("https://notebooklm.google.com/")
        await page.wait_for_selector("text=New Notebook", timeout=15000)
        await page.click("text=New Notebook")
        
        try:
            print("Looking for Upload files button...")
            async with page.expect_file_chooser() as fc_info:
                await page.locator("text=Upload files").click()
            file_chooser = await fc_info.value
            print("File chooser caught!")
            await file_chooser.set_files("Wipro2.pdf")
            print("File set successfully!")
            await page.wait_for_timeout(3000)
        except Exception as e:
            print("Failed to upload:", e)
            
        # Save screenshot
        await page.screenshot(path="debug_notebook.png")
        
        # Dump HTML
        html = await page.content()
        with open("debug_notebook.html", "w") as f:
            f.write(html)
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(debug_upload())
