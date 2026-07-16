"""
IW-20 SERPScreenshot — Capture Visuelle SERP
Iron Warrior #20 — Audit visuel, screenshot PNG.
Aucun sur RapidAPI.
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from urllib.parse import quote_plus
import sys
sys.path.insert(0, '/home/user/iron_warriors/shared')
from base import create_app, get_timestamp, measure_latency
import time
import io

app = create_app("IW-20 SERPScreenshot", "Capture visuelle SERP — screenshot PNG audit")

class ScreenshotMeta(BaseModel):
    query: str
    engine: str
    screenshot_url: str
    width: int
    height: int
    timestamp: str
    latency_ms: int

@app.get("/screenshot", response_class=StreamingResponse)
async def serp_screenshot(
    q: str = Query(..., description="Search query"),
    engine: str = Query("google", description="google, bing, duckduckgo"),
    width: int = Query(1280, ge=320, le=2560),
    height: int = Query(800, ge=480, le=1600),
    full_page: bool = Query(False, description="Capture full page"),
    gl: str = Query("us"),
    hl: str = Query("en"),
):
    """Returns a PNG screenshot of the SERP."""
    start = time.time()

    if engine == "google":
        url = f"https://www.google.com/search?q={quote_plus(q)}&gl={gl}&hl={hl}"
    elif engine == "bing":
        url = f"https://www.bing.com/search?q={quote_plus(q)}"
    elif engine == "duckduckgo":
        url = f"https://duckduckgo.com/?q={quote_plus(q)}"
    else:
        raise HTTPException(status_code=400, detail="Engine must be google, bing, or duckduckgo")

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise HTTPException(status_code=500, detail="Playwright not installed. Run: pip install playwright && playwright install chromium")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Let results render

            if full_page:
                png = await page.screenshot(full_page=True)
            else:
                png = await page.screenshot()

            await browser.close()

        return StreamingResponse(
            io.BytesIO(png),
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=serp_{engine}_{q[:20]}.png"}
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Screenshot failed: {e}")

@app.get("/screenshot/meta", response_model=ScreenshotMeta)
async def screenshot_meta(
    q: str = Query(...),
    engine: str = Query("google"),
    width: int = Query(1280),
    height: int = Query(800),
):
    """Returns metadata about the screenshot endpoint."""
    return ScreenshotMeta(
        query=q, engine=engine,
        screenshot_url=f"/screenshot?q={quote_plus(q)}&engine={engine}&width={width}&height={height}",
        width=width, height=height,
        timestamp=get_timestamp(), latency_ms=0,
    )
