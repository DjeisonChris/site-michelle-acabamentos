import requests
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from PIL import Image
import os
import json
import random

# --- CONSTANTES GLOBAIS PARA MICHELLE ACABAMENTOS ---
FONT_PATH = "DejaVuSans.ttf"
URL_PRODUTOS = "https://script.google.com/macros/s/AKfycbyOLlP99avxI7kIRXBTgKx_oDt1PMBa2MpOyCZVv5H54AB4KCXYGeUk4YlwjW_oj3J2rg/exec"
URL_LOGO = "https://i.ibb.co/0HmBNqd/Logo-6.png"
URL_BANNER_MICHELLE = "https://ofertasmichelle.com.br/banner/banner.jpg"  # <-- URL ADICIONADA
URL_WHATSAPP = "https://wa.me/47996970021"
URL_SITE = "https://ofertasmichelle.com.br"

def limpar_preco(preco_str):
    if not preco_str: return 0.0
    if isinstance(preco_str, (int, float)): return float(preco_str)
    texto_limpo = str(preco_str).replace('R$', '').strip().replace('.', '').replace(',', '.')
    if not texto_limpo: return 0.0
    return float(texto_limpo)

def formatar_data_br(data_iso):
    if not data_iso: return ''
    try:
        data_apenas = str(data_iso).split('T')[0]
        ano, mes, dia = data_apenas.split('-')
        return f"{dia}/{mes}/{ano}"
    except:
        return str(data_iso)

class PDF(FPDF):
    def header(self):
        if self.page_no() <= 2: return
        self.image(URL_LOGO, 10, 8, 33, link=URL_SITE)
        self.set_y(15)
        self.set_font('DejaVu', 'B', 15)
        self.cell(0, 7, 'Catálogo de Ofertas', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font('DejaVu', 'B', 12)
        self.set_text_color(195, 19, 39)
        self.cell(0, 7, 'Michelle Acabamentos', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C', link=URL_SITE)
        self.set_text_color(0, 0, 0)
        self.ln(15)

    def footer(self):
        if self.page_no() <= 2: return
        self.set_y(-15)
        self.set_font('DejaVu', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', align='C')

# ... (O resto do código que não foi alterado continua aqui) ...

def renderizar_produto(pdf, produto):
    try:
        true_values = ['true', 'verdadeiro', 'x', 'sim', 's']
        is_out_of_stock = str(produto.get('isOutOfStock')).lower() in true_values
        
        if is_out_of_stock: return

        pdf.add_page()
        
        img_response = requests.get(produto['image'])
        img_path = os.path.join('imagens_temp', f"{produto['id']}.jpg")
        with open(img_path, 'wb') as f: f.write(img_response.content)

        compressed_img_path = os.path.join('imagens_temp', f"compressed_{produto['id']}.jpg")
        with Image.open(img_path) as img:
            if img.mode == 'RGBA' or img.mode == 'LA' or (img.mode == 'P' and 'transparency' in img.info):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, (0, 0), img.convert('RGBA'))
                img = background
            else:
                img = img.convert('RGB')
            
            img.save(compressed_img_path, 'JPEG', quality=85, optimize=True)
            img_w, img_h = img.size

        max_w, max_h = 70, 90
        ratio = min(max_w / img_w, max_h / img_h)
        pdf_img_w, pdf_img_h = img_w * ratio, img_h * ratio
        x_pos = (pdf.w - pdf_img_w) / 2
        pdf.image(compressed_img_path, x=x_pos, w=pdf_img_w, h=pdf_img_h)
        pdf.ln(5)

        pdf.set_font('DejaVu', 'B', 16)
        pdf.multi_cell(0, 8, produto['name'], align='C')
        pdf.ln(2)

        pdf.set_font('DejaVu', '', 11)
        codigo = str(produto.get('code', 'N/A')).split('.')[0]
        marca = produto.get('brand', 'N/A')
        pdf.cell(0, 7, f"Código: {codigo} | Marca: {marca}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(3)

        old_price = limpar_preco(produto.get('oldPrice'))
        new_price = limpar_preco(produto.get('price'))
        
        if old_price > new_price:
            pdf.set_font('DejaVu', 'I', 12)
            pdf.set_text_color(128, 128, 128)
            pdf.cell(0, 7, f"De: R$ {old_price:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        if new_price > 0:
            pdf.set_font('DejaVu', 'B', 22)
            pdf.set_text_color(40, 167, 69)
            pdf.cell(0, 10, f"Por: R$ {new_price:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        pdf.set_text_color(0, 0, 0)
        
        info_adicional = produto.get('infoAdicional')
        if info_adicional:
            pdf.ln(4)
            pdf.set_font('DejaVu', 'B', 10)
            pdf.set_fill_color(254, 252, 235)
            pdf.set_text_color(133, 77, 14)
            
            text_width = pdf.get_string_width(info_adicional)
            cell_width = text_width + 10
            cell_x = (pdf.w - cell_width) / 2
            
            pdf.set_x(cell_x)
            pdf.multi_cell(cell_width, 7, info_adicional, align='C', fill=True, border=1)
            pdf.set_text_color(0, 0, 0)
        
        pdf.ln(8)
        pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())

    except Exception as e:
        print(f"  - Erro ao processar o produto {produto.get('id', '')} ({produto.get('name', '')}): {e}")

# --- FUNÇÃO DA PÁGINA DE CAPA ATUALIZADA ---
def criar_pagina_de_capa(pdf, config):
    print("Criando a página de capa...")
    pdf.add_page()
    pdf.image(URL_LOGO, x=pdf.w / 2 - 35, y=15, w=70, link=URL_SITE)

    # --- INÍCIO DA MODIFICAÇÃO: Bloco para baixar e inserir o banner ---
    try:
        print("Baixando banner do site...")
        caminho_banner_temp = os.path.join('imagens_temp', 'banner_michelle.jpg')
        response = requests.get(URL_BANNER_MICHELLE)
        response.raise_for_status() # Lança um erro se o download falhar
        with open(caminho_banner_temp, 'wb') as f:
            f.write(response.content)
        # Posiciona o banner abaixo do logo. x=10 e w=128.5 são para A5 com margem de 10mm
        pdf.image(caminho_banner_temp, x=10, y=65, w=128.5)
        pdf.set_y(130) # Pula o cursor para depois do banner
    except Exception as e:
        print(f"Aviso: Não foi possível baixar o banner do site. O PDF será gerado sem ele. Erro: {e}")
        pdf.set_y(110) # Se não houver banner, posiciona o cursor mais acima
    # --- FIM DA MODIFICAÇÃO ---
    
    pdf.set_font('DejaVu', 'B', 12)
    
    data_inicio_str = config.get('data_inicio', '')
    data_fim_str = config.get('data_fim', '')
    if data_inicio_str and data_fim_str:
        texto_validade = f"Ofertas Válidas de {formatar_data_br(data_inicio_str)} a {formatar_data_br(data_fim_str)}"
    else:
        texto_validade = "Consulte a validade das ofertas na loja"
    pdf.multi_cell(0, 6, texto_validade, align='C')
    
    pdf.ln(10)
    pdf.set_font('DejaVu', 'B', 11)
    pdf.cell(0, 7, "Nossos Contatos", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font('DejaVu', '', 9)
    pdf.multi_cell(0, 5, "(47) 99697-0021 | (47) 99697-0090\nR. 2350 Catágua, Nº 196 - Itapoá, SC", align='C')
    pdf.ln(5)
    pdf.set_font('DejaVu', 'B', 11)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 7, "Clique nos links abaixo!", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font('DejaVu', '', 10)
    pdf.cell(0, 7, "Fale conosco pelo WhatsApp", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C', link=URL_WHATSAPP)
    pdf.cell(0, 7, "Acesse nosso site de ofertas online", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C', link=URL_SITE)
    pdf.set_text_color(0, 0, 0)

# ... (O resto do código que não foi alterado continua aqui, como criar_pagina_indice, etc.) ...
def criar_pagina_indice(pdf, categorias, links_map, link_destaques, tem_destaques):
    print("Desenhando o índice na página reservada...")
    pdf.set_font('DejaVu', 'B', 24)
    pdf.cell(0, 20, "Índice", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)

    if tem_destaques:
        pdf.set_font('DejaVu', 'B', 14)
        pdf.set_text_color(255, 58, 58) # Vermelho destaque
        pdf.cell(0, 10, "★ Ofertas Imperdíveis ★", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C', link=link_destaques)
        pdf.ln(5)

    pdf.set_font('DejaVu', '', 12)
    pdf.set_text_color(0, 102, 204) # Azul para categorias
    for cat_nome in categorias:
        pdf.cell(0, 10, cat_nome, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C', link=links_map[cat_nome])
    
    pdf.set_text_color(0, 0, 0)

def criar_pagina_destaques(pdf, produtos_destaque, link_destaques):
    print("Criando a página de Ofertas Imperdíveis...")
    pdf.add_page()
    pdf.set_link(link_destaques, y=0)
    
    pdf.set_font('DejaVu', 'B', 28)
    pdf.set_text_color(195, 19, 39)
    pdf.set_y(80)
    pdf.multi_cell(0, 15, "Ofertas\nImperdíveis", align='C')
    pdf.set_text_color(0, 0, 0)
    
    for produto in produtos_destaque:
        renderizar_produto(pdf, produto)

def criar_pagina_propaganda(pdf, propaganda_item):
    print(f"Criando página de propaganda: {propaganda_item.get('titulo')}")
    pdf.add_page()
    pdf.set_fill_color(195, 19, 39) 
    pdf.rect(0, 0, pdf.w, pdf.h, 'F') 
    
    pdf.set_y(pdf.h / 3)
    pdf.set_font('DejaVu', 'B', 26)
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(0, 15, propaganda_item.get('titulo', ''), align='C')
    
    pdf.ln(15)
    
    pdf.set_font('DejaVu', 'B', 14)
    
    button_w = 80
    button_h = 12
    button_x = (pdf.w - button_w) / 2
    button_y = pdf.get_y()
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(button_x, button_y, button_w, button_h, 'F')
    
    pdf.set_text_color(195, 19, 39)
    pdf.set_xy(button_x, button_y)
    pdf.cell(button_w, button_h, propaganda_item.get('texto_botao', 'Ver Ofertas'), align='C', link=propaganda_item.get('link_botao', URL_SITE))
    
    pdf.set_text_color(0, 0, 0) 

def gerar_catalogo_pdf():
    if not os.path.exists(FONT_PATH):
        print(f"ERRO: Fonte '{FONT_PATH}' não encontrada.")
        return
    
    print("Iniciando a geração do catálogo para Michelle Acabamentos...")
    try:
        response = requests.get(URL_PRODUTOS, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        produtos = data.get('products', [])
        categorias_info = data.get('categorias', [])
        config = data.get('config', {})
        propaganda_data = data.get('propaganda', [])

        if not produtos:
            print("ERRO CRÍTICO: Nenhum produto encontrado na API.")
            return
            
    except requests.exceptions.RequestException as e:
        print(f"ERRO DE REDE: Não foi possível buscar os dados. Verifique sua conexão. Detalhes: {e}")
        return
    except json.JSONDecodeError:
        print("ERRO CRÍTICO: A resposta da API não é um JSON válido.")
        return

    mapa_categorias = {cat['categoria']: cat['nome_exibicao'] for cat in categorias_info}
    
    categorias_ativas = sorted(
        [mapa_categorias.get(cat_id) for cat_id in set(p.get('category') for p in produtos if p.get('category')) if mapa_categorias.get(cat_id)],
        key=lambda x: x if x is not None else ""
    )
    
    true_values = ['true', 'verdadeiro', 'x', 'sim', 's']
    
    produtos_destaque = [p for p in produtos if str(p.get('isDestaque')).lower() in true_values]
    
    propagandas_ativas = [p for p in propaganda_data if str(p.get('ativo')).lower() in true_values]
    random.shuffle(propagandas_ativas) 
    propaganda_iterator = iter(propagandas_ativas)

    pdf = PDF(format='A5')
    pdf.add_font('DejaVu', '', FONT_PATH)
    pdf.add_font('DejaVu', 'B', FONT_PATH)
    pdf.add_font('DejaVu', 'I', FONT_PATH)
    pdf.set_auto_page_break(auto=True, margin=15)
    if not os.path.exists('imagens_temp'): os.makedirs('imagens_temp')
    
    link_destaques = pdf.add_link()
    links_map = {cat_nome: pdf.add_link() for cat_nome in categorias_ativas}
    
    criar_pagina_de_capa(pdf, config)
    
    pdf.add_page()
    indice_page_number = pdf.page_no()
    
    if produtos_destaque:
        criar_pagina_destaques(pdf, produtos_destaque, link_destaques)
    
    for categoria_nome in categorias_ativas:
        categoria_key = next((key for key, val in mapa_categorias.items() if val == categoria_nome), None)
        if not categoria_key: continue

        propaganda_para_mostrar = next(propaganda_iterator, None)
        if propaganda_para_mostrar:
            criar_pagina_propaganda(pdf, propaganda_para_mostrar)
        
        pdf.add_page()
        pdf.set_link(links_map[categoria_nome], y=0) 
        pdf.set_font('DejaVu', 'B', 28)
        pdf.set_y(100)
        pdf.multi_cell(0, 15, f"Categoria:\n{categoria_nome}", align='C')
        
        produtos_da_categoria = [p for p in produtos if p.get('category') == categoria_key]
        for produto in produtos_da_categoria:
            renderizar_produto(pdf, produto)
                
    pdf.page = indice_page_number
    pdf.set_xy(10, 20) 
    criar_pagina_indice(pdf, categorias_ativas, links_map, link_destaques, tem_destaques=bool(produtos_destaque))

    nome_arquivo_final = "catalogo_michelle_acabamentos.pdf"
    pdf.output(nome_arquivo_final)
    print(f"\nCatálogo da Michelle Acabamentos gerado com sucesso! Salvo como: {nome_arquivo_final}")
    
    for file_name in os.listdir('imagens_temp'): os.remove(os.path.join('imagens_temp', file_name))
    os.rmdir('imagens_temp')
    print("Limpeza concluída.")

if __name__ == "__main__":
    gerar_catalogo_pdf()