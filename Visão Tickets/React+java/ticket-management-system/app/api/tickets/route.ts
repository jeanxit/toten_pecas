import { NextResponse } from "next/server"

// This is a mock API endpoint that would be replaced with a real API call in production
export async function GET() {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 800))

  // Mock data - in a real app, you would fetch this from your backend
  const tickets = [
    { id: 1, titulo: "Problema com impressora", urgencia: "Alta", data: "2023-05-15", status: "Pendente" },
    { id: 2, titulo: "Acesso ao sistema bloqueado", urgencia: "Média", data: "2023-05-16", status: "Pendente" },
    { id: 3, titulo: "Computador não liga", urgencia: "Alta", data: "2023-05-17", status: "Pendente" },
    { id: 4, titulo: "Instalação de software", urgencia: "Baixa", data: "2023-05-14", status: "Em Andamento" },
    { id: 5, titulo: "Configuração de email", urgencia: "Média", data: "2023-05-13", status: "Em Andamento" },
    { id: 6, titulo: "Troca de teclado", urgencia: "Baixa", data: "2023-05-10", status: "Finalizado" },
    { id: 7, titulo: "Atualização de sistema", urgencia: "Média", data: "2023-05-09", status: "Finalizado" },
    { id: 8, titulo: "Recuperação de arquivos", urgencia: "Alta", data: "2023-05-08", status: "Finalizado" },
    { id: 9, titulo: "Configuração de VPN", urgencia: "Média", data: "2023-05-07", status: "Finalizado" },
    { id: 10, titulo: "Problema com monitor", urgencia: "Média", data: "2023-05-18", status: "Pendente" },
    { id: 11, titulo: "Erro no sistema ERP", urgencia: "Alta", data: "2023-05-19", status: "Pendente" },
    { id: 12, titulo: "Configuração de rede", urgencia: "Baixa", data: "2023-05-12", status: "Em Andamento" },
    { id: 13, titulo: "Atualização de antivírus", urgencia: "Baixa", data: "2023-05-06", status: "Finalizado" },
    { id: 14, titulo: "Problema com internet", urgencia: "Alta", data: "2023-05-20", status: "Pendente" },
  ]

  return NextResponse.json(tickets)
}
