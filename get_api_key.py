from playwright.sync_api import sync_playwright
import time

def get_rapidapi_key():
    print("Iniciando Playwright para obtener la API key de RapidAPI...")
    with sync_playwright() as p:
        # Usamos no headless para ver si hay captchas o problemas
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        
        try:
            # Ir al login de RapidAPI
            print("Navegando a RapidAPI...")
            page.goto("https://rapidapi.com/auth/login")
            page.wait_for_load_state("networkidle")
            
            # Hacer click en "Log In" si hay pantalla previa o rellenar form
            print("Rellenando credenciales...")
            # Rellenar email
            page.fill('input[type="email"]', 'mnlvicentefernandez@gmail.com', timeout=10000)
            # Rellenar pass
            page.fill('input[type="password"]', 'Quiniela1', timeout=10000)
            
            # Botón login (asumiendo botón genérico de submit o button)
            page.click('button[type="submit"], button:has-text("Log In"), button:has-text("Login")')
            
            print("Esperando a que cargue el dashboard...")
            page.wait_for_timeout(5000)
            
            # Ir a los settings del proyecto o API-Football específicamente
            print("Navegando a API-Football...")
            page.goto("https://rapidapi.com/api-sports/api/api-football")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)
            
            # Extraer headers de código de ejemplo donde viene la key
            print("Buscando X-RapidAPI-Key...")
            code_snippets = page.locator("code").all_inner_texts()
            
            api_key = None
            for snippet in code_snippets:
                if "X-RapidAPI-Key" in snippet:
                    import re
                    # Buscar el patrón 'X-RapidAPI-Key': 'key'
                    match = re.search(r"'X-RapidAPI-Key':\s*'([^']+)'", snippet)
                    if match:
                        api_key = match.group(1)
                        break
            
            if api_key:
                print(f"\n¡ÉXITO! API Key encontrada: {api_key}")
                with open(".env", "w") as f:
                    f.write(f"RAPIDAPI_KEY={api_key}\n")
                print("Guardada en archivo .env")
            else:
                print("\nNo se pudo encontrar la API Key en el código. Puede que la página tenga otra estructura o el login fallara.")
                # Guardar captura por si acaso
                page.screenshot(path="rapidapi_error.png")
                print("Captura guardada en rapidapi_error.png")
                
        except Exception as e:
            print(f"Error durante el proceso: {e}")
            page.screenshot(path="rapidapi_error.png")
            
        finally:
            browser.close()

if __name__ == "__main__":
    get_rapidapi_key()
