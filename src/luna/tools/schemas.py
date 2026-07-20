TOOLS_SCHEMA = [
    {
        "name": "listar_servicos",
        "description": "Lista os servicos oferecidos pelo pet shop, com preco e duracao.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "consultar_cliente",
        "description": "Busca um cliente pelo telefone no CRM, trazendo os pets cadastrados e "
                        "os ultimos agendamentos. Use quando o cliente informar o telefone, pra "
                        "reconhecer se ja e cliente antigo e puxar os dados dele/dos pets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "telefone": {"type": "string", "description": "Telefone informado pelo cliente"},
            },
            "required": ["telefone"],
        },
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
    {
        "name": "agendar",
        "description": "Efetiva um agendamento no CRM. So chame isso DEPOIS que o cliente "
                        "confirmar explicitamente o resumo (servico, pet, data/hora, tutor, "
                        "telefone) que voce apresentou antes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cliente_nome": {"type": "string", "description": "Nome do tutor"},
                "cliente_telefone": {"type": "string", "description": "Telefone com DDD"},
                "pet_nome": {"type": "string"},
                "pet_porte": {"type": "string", "description": "Pequeno, Medio ou Grande, se souber"},
                "servico_nome": {"type": "string"},
                "data_hora": {"type": "string", "description": "Formato AAAA-MM-DD HH:MM"},
            },
            "required": ["cliente_nome", "cliente_telefone", "pet_nome", "servico_nome", "data_hora"],
        },
    },
    {
        "name": "cancelar",
        "description": "Cancela um agendamento existente no CRM. So chame isso DEPOIS que o "
                        "cliente confirmar explicitamente o resumo (servico, data/hora) que voce "
                        "apresentou antes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cliente_telefone": {"type": "string", "description": "Telefone com DDD"},
                "data_hora": {"type": "string",
                              "description": "Data/hora do agendamento a cancelar, formato AAAA-MM-DD HH:MM"},
            },
            "required": ["cliente_telefone", "data_hora"],
        },
    },
]
