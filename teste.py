import bcrypt
from datetime import datetime
from supabase import create_client, Client
from gotrue.errors import AuthApiError

# Config Supabase
SUPABASE_URL = "https://hapxgagbnbnncigwjqzy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhcHhnYWdibmJubmNpZ3dqcXp5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTY2MTUyNywiZXhwIjoyMDY1MjM3NTI3fQ.IHrGZC64fre1FeTZ7uTDmzgiQ7o7bhN4Tl-WGOGQQE8"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def cadastrar_usuario_auth(
    login: str,
    email: str,
    senha: str,
    nome: str,
    telefone: str | None,
    tipo_acesso_id: int,
    perfil_usuario_id: int,
    status: str = "ativo"
):
    try:
        # 1. Criar usuário no Auth
        auth_response = supabase.auth.admin.create_user({
            "email": email,
            "password": senha,
            "email_confirm": True,
            "user_metadata": {"login": login}
        })

        if not auth_response.user:
            print("❌ Falha ao criar usuário no Auth.")
            return

        auth_user_id = auth_response.user.id
        print(f"✅ Usuário criado no Auth com ID: {auth_user_id}")

        # 2. Criar hash da senha para tabela usuarios
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # 3. Montar dados para tabela usuarios
        agora = datetime.utcnow().isoformat()
        dados_usuario = {
            "user_id": auth_user_id,     # vincula com o ID do Auth
            "login": login,
            "telefone": telefone,
            "email": email,
            "nome": nome,
            "senha_hash": senha_hash,
            "tipo_acesso_id": tipo_acesso_id,
            "perfil_usuario_id": perfil_usuario_id,
            "status": status,
            "criado_em": agora,
            "atualizado_em": agora
        }

        # 4. Inserir na tabela usuarios
        db_response = supabase.table("usuarios").insert(dados_usuario).execute()

        if db_response.error is not None:
            # Se erro ao inserir no banco, apaga usuário criado no Auth para manter consistência
            print("❌ Erro ao inserir no banco de dados:", db_response.error)
            print("⏳ Tentando deletar usuário criado no Auth para manter consistência...")
            try:
                supabase.auth.admin.delete_user(auth_user_id)
                print("✅ Usuário no Auth deletado com sucesso.")
            except Exception as del_err:
                print("⚠️ Falha ao deletar usuário no Auth:", del_err)
            return

        if db_response.data:
            print("✅ Usuário cadastrado com sucesso e vinculado ao Auth.")
        else:
            print("⚠️ Nenhum dado retornado ao inserir usuário.")

    except AuthApiError as auth_err:
        if "already been registered" in str(auth_err):
            print("⚠️ Este e-mail já está em uso. Tente outro.")
        else:
            print("❌ Erro na autenticação:", auth_err)

    except Exception as e:
        print("❌ Erro geral:", e)

# Exemplo de uso:
cadastrar_usuario_auth(
    login="jej",
    email="jean@app.com",
    senha="SenhaForte123!",
    nome="Maria Silva",
    telefone="11988887777",
    tipo_acesso_id=3,        # mantenha um ID válido
    perfil_usuario_id=3,     # mantenha um ID válido
    status="ativo"
)
