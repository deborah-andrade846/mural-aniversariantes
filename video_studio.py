"""Estúdio de vídeo do mural (função do administrador).

Gera, no navegador, um vídeo com um aniversariante por quadro (estilo TV)
para anexar em comunicados. Usado a partir do painel admin em app.py.
"""
import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd


def _montar_slides(df_mes, nome_mes):
    """Monta a lista de cards (dados) para o vídeo, na ordem por dia."""
    slides = []
    for _, row in df_mes.iterrows():
        nome = str(row.get("nome", "")).strip().title()
        dia = int(row["data_nascimento"].day) if pd.notna(row["data_nascimento"]) else 0
        curio = str(row.get("curiosidade", "")).strip()
        if curio.lower() in ("", "nan", "none", "null"):
            curio = ""
        foto = str(row.get("foto_url", "")).strip()

        partes = nome.split()
        if len(partes) >= 2:
            iniciais = (partes[0][0] + partes[-1][0]).upper()
        elif partes:
            iniciais = partes[0][:2].upper()
        else:
            iniciais = "?"

        slides.append({
            "nome": nome,
            "dia": dia,
            "curiosidade": curio,
            "foto": foto,
            "iniciais": iniciais,
        })
    return slides


# ── Componente HTML (renderização + gravação no navegador) ────────────────────
_TEMPLATE = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<style>
    *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
    body { font-family:'Inter',sans-serif; color:#0f172a; padding:8px; }

    .painel {
        display:flex; flex-direction:column; gap:14px; align-items:center;
    }
    .controles { display:flex; gap:12px; flex-wrap:wrap; justify-content:center; align-items:center; }
    .btn-gerar {
        font-family:'Inter',sans-serif; font-size:1.05rem; font-weight:700;
        color:#fff; border:none; cursor:pointer;
        padding:0.85rem 1.6rem; border-radius:14px;
        background:linear-gradient(135deg,#0ea5e9,#f472b6);
        box-shadow:0 8px 22px rgba(14,165,233,0.45);
        transition:transform 0.2s ease, filter 0.2s ease;
    }
    .btn-gerar:hover:not(:disabled) { transform:translateY(-2px); filter:brightness(1.05); }
    .btn-gerar:disabled { opacity:0.55; cursor:progress; }
    .status { font-size:0.95rem; font-weight:600; color:#334155; min-height:1.4em; text-align:center; }
    .barra-wrap { width:min(680px,92vw); height:10px; background:#e2e8f0; border-radius:6px; overflow:hidden; display:none; }
    .barra { height:100%; width:0%; background:linear-gradient(90deg,#38bdf8,#f472b6); transition:width 0.2s ease; }

    /* Área de pré-visualização (o próprio canvas da gravação) */
    #preview { width:min(680px,92vw); border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,0.18); background:#0f172a; display:none; }
    #areaDownload { display:none; flex-direction:column; gap:8px; align-items:center; }
    #areaDownload a {
        font-family:'Inter',sans-serif; font-weight:700; text-decoration:none; color:#0f172a;
        background:#bbf7d0; padding:0.7rem 1.4rem; border-radius:12px;
        box-shadow:0 4px 14px rgba(34,197,94,0.3);
    }
    .aviso { font-size:0.85rem; color:#b45309; text-align:center; max-width:680px; }

    /* Estúdio invisível onde os cards são desenhados para virar imagem */
    #studio { position:fixed; top:0; left:0; opacity:0; pointer-events:none; z-index:-1; }
    .vslide {
        position:absolute; top:0; left:0;
        width:1280px; height:720px; overflow:hidden;
        display:flex; align-items:center; gap:56px;
        padding:70px 84px;
        background:linear-gradient(135deg,#fde68a 0%,#fbcfe8 45%,#bae6fd 100%);
        font-family:'Inter',sans-serif;
    }
    .vslide .faixa-topo { position:absolute; top:0; left:0; right:0; height:14px;
        background:linear-gradient(90deg,#38bdf8,#818cf8,#f472b6); }
    .vslide .sub { position:absolute; top:44px; left:84px;
        font-weight:700; letter-spacing:6px; text-transform:uppercase;
        font-size:20px; color:#0369a1; }
    .vslide .mes-tag { position:absolute; top:40px; right:84px;
        font-family:'Playfair Display',serif; font-weight:900; font-size:30px; color:#be185d; }

    .foto-col { flex:0 0 430px; display:flex; align-items:center; justify-content:center; }
    .polaroid { background:#fff; padding:20px 20px 30px; border-radius:8px;
        box-shadow:0 20px 50px rgba(0,0,0,0.22); transform:rotate(-2deg); }
    .foto-quadro { width:390px; height:390px; border-radius:4px; overflow:hidden;
        background:linear-gradient(135deg,#e0e7ff,#c7d2fe); display:flex; align-items:center; justify-content:center; }
    .foto-quadro img { width:100%; height:100%; object-fit:cover; object-position:center 20%; display:block; }
    .foto-iniciais { font-family:'Playfair Display',serif; font-weight:900; font-size:150px; color:#6366f1; }

    .info-col { flex:1; display:flex; flex-direction:column; justify-content:center; }
    .nome { font-family:'Playfair Display',serif; font-weight:900; font-size:74px;
        line-height:1.08; color:#0f172a; }
    .data-badge { align-self:flex-start; margin-top:24px;
        background:#0ea5e9; color:#fff; font-weight:700; font-size:30px;
        padding:12px 30px; border-radius:40px; box-shadow:0 8px 20px rgba(14,165,233,0.4); }
    .curio { margin-top:30px; font-size:30px; font-style:italic; color:#334155;
        line-height:1.4; border-left:6px solid #f472b6; padding-left:22px; max-width:640px; }
    .parabens { margin-top:34px; font-size:34px; font-weight:700; color:#be185d; }

    /* Card de capa */
    .vslide.capa { flex-direction:column; align-items:center; justify-content:center; text-align:center; gap:24px; }
    .capa .capa-sub { font-weight:700; letter-spacing:10px; text-transform:uppercase; font-size:30px; color:#0369a1; }
    .capa .capa-titulo { font-family:'Playfair Display',serif; font-weight:900; font-size:110px; color:#0f172a; line-height:1.05; }
    .capa .capa-mes { color:#be185d; }
    .capa .capa-deco { font-size:64px; letter-spacing:16px; }
    .capa .capa-count { margin-top:10px; font-size:32px; font-weight:600; color:#334155;
        background:rgba(255,255,255,0.6); padding:10px 30px; border-radius:40px; }
    .capa .capa-evento { margin-top:16px; font-size:30px; font-weight:700; color:#0369a1;
        background:rgba(255,255,255,0.72); padding:12px 34px; border-radius:16px;
        box-shadow:0 6px 18px rgba(0,0,0,0.08); }
</style>
</head>
<body>
<div class="painel">
    <div class="controles">
        <button id="btnGerar" class="btn-gerar">🎬 Gerar vídeo</button>
    </div>
    <div id="status" class="status"></div>
    <div id="barraWrap" class="barra-wrap"><div id="barra" class="barra"></div></div>
    <canvas id="preview" width="1280" height="720"></canvas>
    <div id="areaDownload"></div>
    <div id="aviso" class="aviso"></div>
</div>
<div id="studio"></div>

<script>
    var DATA   = __DATA__;
    var SECS   = __SECS__;
    var MES    = "__MES__";
    var EVENTO = __EVENTO__;

    var W = 1280, H = 720, FPS = 30, FADE_MS = 500;

    var btn      = document.getElementById('btnGerar');
    var statusEl = document.getElementById('status');
    var barraWrap= document.getElementById('barraWrap');
    var barra    = document.getElementById('barra');
    var studio   = document.getElementById('studio');
    var preview  = document.getElementById('preview');
    var areaDown = document.getElementById('areaDownload');
    var avisoEl  = document.getElementById('aviso');

    function esc(s){
        return String(s == null ? '' : s)
            .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
            .replace(/"/g,'&quot;');
    }

    // Carrega a foto como blob (URL local) para não "contaminar" o canvas.
    function carregarFoto(url){
        return new Promise(function(resolve){
            if(!url){ resolve(null); return; }
            fetch(url, {mode:'cors'}).then(function(r){
                if(!r.ok) throw new Error('http');
                return r.blob();
            }).then(function(blob){
                var obj = URL.createObjectURL(blob);
                var img = new Image();
                img.onload = function(){ resolve(img); };
                img.onerror = function(){ resolve(null); };
                img.src = obj;
            }).catch(function(){ resolve(null); });
        });
    }

    function montarCapa(){
        var el = document.createElement('div');
        el.className = 'vslide capa';
        var eventoHtml = EVENTO
            ? '<div class="capa-evento">' + esc(EVENTO) + '</div>' : '';
        el.innerHTML =
            '<div class="faixa-topo"></div>' +
            '<div class="capa-sub">✦ Celebrações GAFI ✦</div>' +
            '<div class="capa-titulo">Aniversariantes<br>de <span class="capa-mes">' + esc(MES) + '</span></div>' +
            '<div class="capa-deco">🎉 🎂 🎈 🎊 🎁</div>' +
            '<div class="capa-count">' + DATA.length + ' aniversariante' + (DATA.length===1?'':'s') + '</div>' +
            eventoHtml;
        return el;
    }

    function montarSlide(item, imgEl){
        var el = document.createElement('div');
        el.className = 'vslide';
        var fotoInterna = imgEl
            ? ''  /* a imagem é anexada via DOM abaixo */
            : '<div class="foto-iniciais">' + esc(item.iniciais) + '</div>';
        var curioHtml = item.curiosidade
            ? '<div class="curio">"' + esc(item.curiosidade) + '"</div>' : '';
        el.innerHTML =
            '<div class="faixa-topo"></div>' +
            '<div class="sub">✦ Celebrações GAFI ✦</div>' +
            '<div class="mes-tag">' + esc(MES) + '</div>' +
            '<div class="foto-col">' +
                '<div class="polaroid"><div class="foto-quadro" id="fq"></div></div>' +
            '</div>' +
            '<div class="info-col">' +
                '<div class="nome">' + esc(item.nome) + '</div>' +
                '<div class="data-badge">🎉 ' + item.dia + ' de ' + esc(MES) + '</div>' +
                curioHtml +
                '<div class="parabens">Feliz aniversário! 🥳</div>' +
            '</div>';
        var fq = el.querySelector('#fq');
        if(imgEl){ fq.appendChild(imgEl); }
        else { fq.innerHTML = '<div class="foto-iniciais">' + esc(item.iniciais) + '</div>'; }
        return el;
    }

    function escolherMime(){
        var cands = [
            'video/mp4;codecs=avc1.42E01E',
            'video/mp4',
            'video/webm;codecs=vp9',
            'video/webm;codecs=vp8',
            'video/webm'
        ];
        for(var i=0;i<cands.length;i++){
            if(window.MediaRecorder && MediaRecorder.isTypeSupported(cands[i])) return cands[i];
        }
        return '';
    }

    async function renderFrames(){
        var frames = [];
        // capa
        var capa = montarCapa();
        studio.appendChild(capa);
        await document.fonts.ready;
        var cShot = await html2canvas(capa, {width:W, height:H, scale:1, backgroundColor:null, useCORS:true, logging:false});
        frames.push(cShot);
        studio.removeChild(capa);

        for(var i=0;i<DATA.length;i++){
            statusEl.textContent = 'Renderizando card ' + (i+1) + ' de ' + DATA.length + '...';
            var img = await carregarFoto(DATA[i].foto);
            var slide = montarSlide(DATA[i], img);
            studio.appendChild(slide);
            // pequena espera para o layout/imagem assentar
            await new Promise(function(r){ setTimeout(r, 40); });
            var shot = await html2canvas(slide, {width:W, height:H, scale:1, backgroundColor:null, useCORS:true, logging:false});
            frames.push(shot);
            studio.removeChild(slide);
            barra.style.width = Math.round(((i+1)/DATA.length)*60) + '%';
        }
        return frames;
    }

    function gravar(frames){
        return new Promise(function(resolve, reject){
            var ctx = preview.getContext('2d');
            var stream = preview.captureStream(FPS);
            var mime = escolherMime();
            var opts = mime ? {mimeType:mime, videoBitsPerSecond:5000000} : {videoBitsPerSecond:5000000};
            var rec;
            try { rec = new MediaRecorder(stream, opts); }
            catch(e){ reject(e); return; }

            var chunks = [];
            rec.ondataavailable = function(e){ if(e.data && e.data.size) chunks.push(e.data); };
            rec.onstop = function(){
                var tipo = (mime && mime.indexOf('mp4')>=0) ? 'mp4' : 'webm';
                var blob = new Blob(chunks, {type: (mime || 'video/webm')});
                resolve({blob:blob, ext:tipo});
            };

            var holdMs = SECS*1000;
            var n = frames.length;
            var t0 = performance.now();
            rec.start();

            function frame(now){
                var t = now - t0;
                var idx = Math.floor(t / holdMs);
                if(idx >= n){ rec.stop(); return; }
                var local = t - idx*holdMs;
                ctx.clearRect(0,0,W,H);
                if(local < FADE_MS && idx > 0){
                    ctx.globalAlpha = 1;
                    ctx.drawImage(frames[idx-1], 0, 0, W, H);
                    ctx.globalAlpha = Math.min(1, local/FADE_MS);
                    ctx.drawImage(frames[idx], 0, 0, W, H);
                    ctx.globalAlpha = 1;
                } else {
                    ctx.drawImage(frames[idx], 0, 0, W, H);
                }
                var prog = 60 + Math.round((t/(n*holdMs))*40);
                barra.style.width = Math.min(100, prog) + '%';
                requestAnimationFrame(frame);
            }
            requestAnimationFrame(frame);
        });
    }

    async function gerar(){
        btn.disabled = true;
        areaDown.style.display = 'none';
        areaDown.innerHTML = '';
        avisoEl.textContent = '';
        barraWrap.style.display = 'block';
        preview.style.display = 'block';
        barra.style.width = '0%';

        if(!window.MediaRecorder){
            statusEl.textContent = '';
            avisoEl.textContent = 'Seu navegador não suporta gravação de vídeo (MediaRecorder). Use um Chrome/Edge atualizado.';
            btn.disabled = false;
            return;
        }

        try {
            statusEl.textContent = 'Preparando...';
            var frames = await renderFrames();
            statusEl.textContent = 'Gravando o vídeo...';
            var out = await gravar(frames);

            var url = URL.createObjectURL(out.blob);
            var nome = 'mural-aniversariantes-' + MES.toLowerCase() + '.' + out.ext;
            var a = document.createElement('a');
            a.href = url; a.download = nome;
            a.textContent = '⬇️ Baixar ' + nome;
            areaDown.appendChild(a);
            areaDown.style.display = 'flex';
            statusEl.textContent = '✅ Vídeo pronto!';
            barra.style.width = '100%';

            if(out.ext !== 'mp4'){
                avisoEl.textContent = 'Obs.: seu navegador gerou o arquivo em .webm (não suporta gravar MP4 direto). ' +
                    'O .webm funciona no computador e no WhatsApp Web; se precisar de MP4 para celular, me avise.';
            }
        } catch(err){
            statusEl.textContent = '';
            avisoEl.textContent = 'Não foi possível gerar o vídeo. ' +
                'Isso costuma acontecer quando alguma foto bloqueia o uso (CORS). Detalhe: ' + (err && err.message ? err.message : err);
        } finally {
            btn.disabled = false;
        }
    }

    btn.addEventListener('click', gerar);
</script>
</body>
</html>
"""

def render_estudio(supabase, mes_sel, segs, meses_ptbr, data_evento="", local_evento=""):
    """Renderiza o estúdio de vídeo na área principal (uso pelo admin)."""
    nome_mes = meses_ptbr[mes_sel]

    st.title("🎬 Estúdio de Vídeo do Mural")
    st.caption(
        "Vídeo com um aniversariante por vez (estilo TV) para os comunicados. "
        "É gerado **no seu navegador**. Para voltar ao mural, desmarque "
        "*Abrir estúdio de vídeo* no painel de administração."
    )

    try:
        with st.spinner("Carregando aniversariantes..."):
            dados = supabase.table("aniversariantes").select("*").execute().data or []
    except Exception:
        st.error("Não foi possível conectar ao banco de dados. Tente novamente.")
        return

    if not dados:
        st.info("📭 Nenhum aniversariante cadastrado ainda.")
        return

    df = pd.DataFrame(dados)
    df["data_nascimento"] = pd.to_datetime(df["data_nascimento"], errors="coerce")
    df_mes = df[df["data_nascimento"].dt.month == mes_sel].copy()

    if df_mes.empty:
        st.info(f"📅 Nenhum aniversariante em {nome_mes}.")
        return

    df_mes = df_mes.sort_values(by="data_nascimento", key=lambda s: s.dt.day)
    slides = _montar_slides(df_mes, nome_mes)

    st.caption(
        f"🎂 {len(slides)} aniversariante(s) em {nome_mes}. "
        f"Duração aproximada do vídeo: {len(slides) * segs + segs} s."
    )

    _partes_ev = []
    if str(data_evento).strip():
        _partes_ev.append("📅 " + str(data_evento).strip())
    if str(local_evento).strip():
        _partes_ev.append("📍 " + str(local_evento).strip())
    evento_txt = "   •   ".join(_partes_ev)

    payload = json.dumps(slides, ensure_ascii=False)
    html = (
        _TEMPLATE
        .replace("__DATA__", payload)
        .replace("__SECS__", str(segs))
        .replace("__EVENTO__", json.dumps(evento_txt, ensure_ascii=False))
        .replace("__MES__", nome_mes)
    )
    components.html(html, height=760, scrolling=True)

    st.info(
        "💡 Dica: o vídeo é gerado no seu navegador. Se alguma foto não aparecer, "
        "ela é substituída pelas iniciais da pessoa (isso evita erro na geração). "
        "Recomendo usar o **Chrome** ou **Edge** atualizados."
    )
