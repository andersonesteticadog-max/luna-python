import sqlite3

# Caminho relativo: assume que os scripts sao rodados a partir da raiz do
# projeto (mesma convencao do load_dotenv() no config.py).
DB_PATH = "crm.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL,
    duracao_min INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    telefone TEXT
);

CREATE TABLE IF NOT EXISTS pets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    nome TEXT NOT NULL,
    especie TEXT,
    porte TEXT,
    raca TEXT
);

CREATE TABLE IF NOT EXISTS agendamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    pet_id INTEGER REFERENCES pets(id),
    servico_id INTEGER NOT NULL REFERENCES servicos(id),
    data_hora TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Agendado',
    observacoes TEXT
);
"""

SERVICOS_SEED = [
    ("Banho Completo - Pequeno", 75.0, 60),
    ("Banho Completo - Medio", 85.0, 60),
    ("Banho Completo - Grande", 95.0, 60),
    ("Tosa na Maquina - Pequeno", 100.0, 90),
    ("Tosa na Maquina - Grande", 140.0, 90),
    ("Tosa na Tesoura - Pequeno", 120.0, 120),
    ("Tosa na Tesoura - Grande", 160.0, 120),
]


def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar():
    """Cria as tabelas se nao existirem e semeia o catalogo de servicos
    na primeira vez (idempotente: nao duplica se rodar de novo)."""
    conn = conectar()
    conn.executescript(SCHEMA)
    ja_tem = conn.execute("SELECT COUNT(*) FROM servicos").fetchone()[0]
    if not ja_tem:
        conn.executemany(
            "INSERT INTO servicos (nome, preco, duracao_min) VALUES (?, ?, ?)",
            SERVICOS_SEED,
        )
        conn.commit()
    conn.close()
