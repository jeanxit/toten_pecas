import { createClient } from '@supabase/supabase-js'
import bcrypt from 'bcryptjs'

// Config Supabase
const SUPABASE_URL = "https://hapxgagbnbnncigwjqzy.supabase.co"
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhcHhnYWdibmJubmNpZ3dqcXp5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTY2MTUyNywiZXhwIjoyMDY1MjM3NTI3fQ.IHrGZC64fre1FeTZ7uTDmzgiQ7o7bhN4Tl-WGOGQQE8"

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

// Função para cadastrar usuário
async function cadastrarUsuarioAuth({
  login,
  email,
  senha,
  nome,
  telefone = null,
  tipo_acesso_id,
  perfil_usuario_id,
  status = 'ativo'
}) {
  try {
    // 1. Criar usuário no Auth
    const { data: authUser, error: authError } = await supabase.auth.admin.createUser({
      email,
      password: senha,
      email_confirm: true,
      user_metadata: { login }
    })

    if (authError) {
      if (authError.message.includes('already been registered')) {
        console.log('⚠️ Este e-mail já está em uso. Tente outro.')
      } else {
        console.error('❌ Erro na autenticação:', authError.message)
      }
      return
    }

    console.log('✅ Usuário criado no Auth com ID:', authUser.id)

    // 2. Gerar hash da senha com bcryptjs
    const senha_hash = await bcrypt.hash(senha, 10)

    // 3. Dados para tabela usuarios
    const agora = new Date().toISOString()
    const dados_usuario = {
      user_id: authUser.id,
      login,
      telefone,
      email,
      nome,
      senha_hash,
      tipo_acesso_id,
      perfil_usuario_id,
      status,
      criado_em: agora,
      atualizado_em: agora
    }

    // 4. Inserir na tabela usuarios
    const { data: dbData, error: dbError } = await supabase
      .from('usuarios')
      .insert(dados_usuario)

    if (dbError) {
      console.error('❌ Erro ao inserir no banco de dados:', dbError.message)
      console.log('⏳ Tentando deletar usuário criado no Auth para manter consistência...')

      // Tenta deletar usuário no Auth
      try {
        const { error: delError } = await supabase.auth.admin.deleteUser(authUser.id)
        if (delError) {
          console.warn('⚠️ Falha ao deletar usuário no Auth:', delError.message)
        } else {
          console.log('✅ Usuário no Auth deletado com sucesso.')
        }
      } catch (err) {
        console.warn('⚠️ Falha ao deletar usuário no Auth:', err.message)
      }
      return
    }

    console.log('✅ Usuário cadastrado com sucesso e vinculado ao Auth.')

  } catch (error) {
    console.error('❌ Erro geral:', error.message)
  }
}

// Exemplo de uso
cadastrarUsuarioAuth({
  login: 'jean05',
  email: 'jean05@app.com',
  senha: 'SenhaForte123!',
  nome: 'Jean teste',
  telefone: '11988887777',
  tipo_acesso_id: 3,
  perfil_usuario_id: 3,
  status: 'ativo'
})
