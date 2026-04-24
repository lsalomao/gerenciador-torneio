Prompt para Mudança de Infraestrutura (PostgreSQL → Supabase)

"Atue como um Desenvolvedor Senior Django. Estamos alterando a infraestrutura de banco de dados do projeto Gerenciador Torneio.

Objetivo: Substituir o PostgreSQL local (Docker) pelo Supabase (PostgreSQL Gerenciado).

Requisitos Técnicos:

Configuração de Database: No settings.py, configure o DATABASES para utilizar a conexão via Connection Pooler do Supabase (porta 6543, modo Transaction), garantindo que as credenciais sejam lidas via variáveis de ambiente (.env).
Ajuste de Docker: Remova o serviço de banco de dados (db ou postgres) do arquivo docker-compose.yml, uma vez que o banco agora é externo. Mantenha os serviços do web (Django) e nginx.
Instalação: Certifique-se de que o psycopg2-binary (ou psycopg[c]) está incluído no requirements.txt.
SSL: Configure o Django para exigir conexão SSL (SSL Mode) com o banco de dados do Supabase para garantir a segurança dos dados em trânsito.
Variáveis de Ambiente: Forneça um exemplo de arquivo .env contendo: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST e DB_PORT.
Por favor, apresente o arquivo settings.py atualizado e o novo docker-compose.yml sem o container de banco de dados local."