import random
import string
from flask import Flask, request, redirect, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter

app = Flask(__name__)

# --- Instrumentação ---
metrics = PrometheusMetrics(app)

# --- Métricas Customizadas ---
links_criados_total = Counter(
    'links_criados_total', 'Total de novos links encurtados criados.')
redirecionamentos_total = Counter(
    'redirecionamentos_total', 'Total de links redirecionados.')

# Banco de dados em memória
url_db = {}


def gerar_codigo_curto(tamanho=6):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(tamanho))


@app.route('/encurtar', methods=['POST'])
def encurtar_url():
    dados = request.get_json()
    if not dados or 'url_longa' not in dados:
        return jsonify({"erro": "URL longa não fornecida"}), 400

    url_longa = dados['url_longa']
    codigo_curto = gerar_codigo_curto()

    while codigo_curto in url_db:
        codigo_curto = gerar_codigo_curto()

    url_db[codigo_curto] = url_longa
    links_criados_total.inc()

    return jsonify({
        "url_longa": url_longa,
        "url_curta": f"{request.host_url}{codigo_curto}"
    }), 201


@app.route('/<string:codigo_curto>', methods=['GET'])
def redirecionar(codigo_curto):
    url_longa = url_db.get(codigo_curto)
    if url_longa:
        redirecionamentos_total.inc()
        return redirect(url_longa, code=302)
    else:
        return jsonify({"erro": "URL curta não encontrada"}), 404


@app.route('/api/links', methods=['GET'])
def listar_links():
    return jsonify(url_db)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
