import asyncio, json, time, random, string, socket
from playwright.async_api import async_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://signup.live.com"

def rand_str(n=8):
    return ''.join(random.choices(string.ascii_lowercase, k=n))

def check_ip():
    import urllib.request
    return urllib.request.urlopen("http://api.ipify.org", timeout=15).read().decode()

def dns_lookup(host):
    try:
        return socket.gethostbyname(host)
    except:
        return None

async def main():
    ip = check_ip()
    print(f"出口IP: {ip}")
    dns = dns_lookup("signup.live.com")
    print(f"DNS signup.live.com: {dns}")
    if not dns:
        print("!! DNS不通, 尝试直接IP访问...")
    
    email = f"{rand_str(10)}@outlook.com"
    password = "Aa!" + rand_str(10) + str(random.randint(10,99))
    print(f"Email: {email} Password: {password}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=UA, viewport={"width":1280,"height":900}, locale="en-US")
        page = await ctx.new_page()
        
        async def page_text():
            return await page.evaluate("() => document.body.innerText.slice(0,300)")
        
        # 打开注册页(带重试)
        print("=== 1. 注册页 ===")
        for attempt in range(3):
            try:
                await page.goto(f"{BASE}/signup?lic=1", wait_until="domcontentloaded", timeout=90000)
                break
            except Exception as e:
                print(f"  加载重试{attempt+1}: {str(e)[:80]}")
                await page.wait_for_timeout(5000)
        await page.wait_for_timeout(8000)
        body = await page_text()
        print(f"  页面: {body[:80]}")
        if not body.strip():
            print("!! 页面空白 — DNS或网络不通")
            return
        
        # 表单流程
        steps = [
            ("email", 'input[type="email"]', email),
            ("password", 'input[type="password"]', password),
        ]
        for name, sel, value in steps:
            print(f"=== {name} ===")
            try:
                inp = page.locator(sel).first
                await inp.wait_for(state="visible", timeout=20000)
                await inp.click()
                for ch in value:
                    await inp.type(ch, delay=random.randint(30,70))
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(5000)
                print(f"  {(await page_text())[:60]}")
            except Exception as e:
                print(f"  {name}: {e}")
        
        # 生日
        print("=== 生日 ===")
        body = await page_text()
        if "detail" in body.lower() or "birth" in body.lower():
            try:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(500)
                n = await page.locator('[role=combobox]').count()
                if n >= 3:
                    await page.evaluate("() => document.querySelectorAll('[role=combobox]')[1].click()")
                    await page.wait_for_timeout(1000)
                    await page.get_by_role("option", name="January").first.click(timeout=8000)
                    await page.wait_for_timeout(1000)
                    for _ in range(8):
                        ok = await page.evaluate("()=>{const cs=[...document.querySelectorAll('[role=combobox]')];const d=cs.find(c=>/day/i.test((c.getAttribute('aria-label')||'')+(c.id||'')))||cs[cs.length-1];if(d){d.click();return 1;}return 0;}")
                        if ok: break
                        await page.wait_for_timeout(600)
                    await page.wait_for_timeout(1000)
                    await page.get_by_role("option", name="15", exact=True).first.click(timeout=8000)
                    await page.wait_for_timeout(1000)
                    yr = page.locator('input[type="text"],input[type="number"]').last
                    await yr.click(); await yr.fill("1990")
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(7000)
            except Exception as e:
                print(f"  生日: {e}")
        
        # 姓名
        body = await page_text()
        if "name" in body.lower():
            print("=== 姓名 ===")
            try:
                fn, ln = page.locator('input').nth(0), page.locator('input').nth(1)
                await fn.click()
                for ch in "John": await fn.type(ch, delay=50)
                await ln.click()
                for ch in "Test": await ln.type(ch, delay=50)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(7000)
            except Exception as e:
                print(f"  姓名: {e}")
        
        # Hold挑战
        for rn in range(10):
            body = await page_text()
            if "hold" not in body.lower() and "prove" not in body.lower():
                break
            print(f"  Hold轮次{rn+1}...")
            try:
                boxes = await page.evaluate("() => {const out=[];for(const f of document.querySelectorAll('iframe')){const r=f.getBoundingClientRect();if(r.width>50&&r.height>30&&r.y>100&&r.y<700)out.push({x:r.x,y:r.y,w:r.width,h:r.height});}return out;}")
                if boxes:
                    b = min(boxes, key=lambda x: x['w'])
                    cx, cy = b['x']+b['w']/2, b['y']+b['h']/2
                    await page.mouse.move(cx-60, cy+20, steps=8)
                    await page.wait_for_timeout(400)
                    await page.mouse.move(cx, cy, steps=6)
                    await page.wait_for_timeout(400)
                    await page.mouse.down()
                    hold_ms = 1500 + random.random()*1200
                    t0 = time.time()
                    while (time.time()-t0)*1000 < hold_ms:
                        await page.mouse.move(cx+random.uniform(-1.5,1.5), cy+random.uniform(-1,1))
                        await page.wait_for_timeout(random.randint(30,80))
                    await page.mouse.up()
                    print(f"  按住{hold_ms:.0f}ms")
                    await page.wait_for_timeout(10000)
            except Exception as e:
                print(f"  Hold: {e}")
        
        # 结果
        print("=== 结果 ===")
        cookies = await ctx.cookies()
        px3 = next((c["value"] for c in cookies if c["name"] == "_px3"), "")
        final_body = await page_text()
        final_url = page.url
        print(f"px3: {px3[:40] if px3 else '(无)'}")
        print(f"URL: {final_url}")
        print(f"页面: {final_body[:250]}")
        
        if "signup" not in final_url:
            print(f"★★★ 成功! 跳转: {final_url}")
        elif "blocked" in final_body.lower():
            print("✗ 被拦截")
        
        await browser.close()
        
        with open("/tmp/result.json", "w") as f:
            json.dump({"email": email, "password": password, "ip": ip,
                       "px3": px3[:60], "final_url": final_url,
                       "final_body": final_body[:300],
                       "cookies": [{"n": c["name"], "v": c["value"][:40]} for c in cookies]}, f, indent=1)
        print(f"\n=== COMBO ===\n{email}----{password}")

asyncio.run(main())
