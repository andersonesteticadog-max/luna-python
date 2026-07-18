TOOLS_SCHEMA = [
    {
        "name": "listar_servicos",
        "description": "Lista os servicos oferecidos pelo pet shop, com preco e duracao.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "consultar_agenda",
        "description": "Consulta os horarios livres do pet shop numa data, considerando a "
                        "duracao do servico desejado (pra nao sugerir horario que nao cabe).",
        "input_schema": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Data no formato AAAA-MM-DD"},
                "duracao_min": {"type": "integer",
                                 "description": "Duracao do servico em minutos"},
            },
            "required": ["data", "duracao_min"],
        },
    },
]
