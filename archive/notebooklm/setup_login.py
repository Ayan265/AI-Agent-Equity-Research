import asyncio
from playwright.async_api import async_playwright

async def run_setup():
    print("Launching browser for initial login...")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./notebooklm_profile",
            executable_path='/usr/bin/brave-browser',
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        await page.goto("https://notebooklm.google.com/")
        
        print("\n========================================================")
        print("ACTION REQUIRED:")
        print("1. Please log in to your Google Account in the browser window.")
        print("2. Wait until you see the NotebookLM dashboard (you should see 'New Notebook').")
        print("3. Once you see the dashboard, press ENTER in this terminal.")
        print("========================================================\n")
        
        input("Press ENTER here after you have successfully logged in... ")
        
        print("Saving session data...")
        await context.close()
        print("Session saved! You can now run the extractor script in headless mode.")

if __name__ == "__main__":
    asyncio.run(run_setup())
