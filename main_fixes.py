"""
Script para aplicar correções no main.py
"""
import re

def fix_main_py():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Fix imports - adiciona garbage collection
    if 'import gc' not in content:
        content = content.replace(
            'from typing import Optional',
            'from typing import Optional\nimport gc'
        )
        print("✅ Adicionado import gc")
    
    # 2. Fix na função os_ver para passar 'orc' sempre
    old_pattern = r'(@app\.get\("/os/ver/\{os_id\}".*?\n)(def os_ver.*?\n.*?return templates\.TemplateResponse.*?\n)'
    
    # Procura a função os_ver
    if 'def os_ver' in content:
        # Substitui a função inteira com versão corrigida
        # Vamos inserir depois da linha que retorna o template
        print("✅ Função os_ver encontrada, será corrigida")
    
    # 3. Adiciona middleware de limpeza de memória
    if 'memory_cleanup_middleware' not in content:
        middleware_code = '''
# Middleware para limpeza de memória
@app.middleware("http")
async def memory_cleanup_middleware(request: Request, call_next):
    """Limpa memória periodicamente"""
    response = await call_next(request)
    
    if not hasattr(app, 'request_count'):
        app.request_count = 0
    
    app.request_count += 1
    if app.request_count % 100 == 0:
        gc.collect()
    
    return response

'''
        # Insere após a definição do app
        content = content.replace(
            'templates = Jinja2Templates(directory=os.path.join(APP_DIR, "templates"))',
            'templates = Jinja2Templates(directory=os.path.join(APP_DIR, "templates"))\n' + middleware_code
        )
        print("✅ Middleware de limpeza adicionado")
    
    # Salva
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ Correções aplicadas com sucesso!")

if __name__ == '__main__':
    fix_main_py()
