"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Navigation } from "@/components/navigation"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from "recharts"
import { useToast } from "@/hooks/use-toast"

// Define the color palette
const COLORS = {
  primary: "#369ED8",
  secondary: "#1C294C",
  tertiary: "#5ABEF5",
  quaternary: "#2E4172",
  success: "#4CAF50",
  warning: "#FFC107",
  danger: "#F44336",
}

// Define ticket type
interface Ticket {
  id: number
  titulo: string
  urgencia: string
  data: string
  status: string
}

export default function Dashboard() {
  const router = useRouter()
  const { toast } = useToast()
  const [selectedStatus, setSelectedStatus] = useState(null)
  const [ticketsToShow, setTicketsToShow] = useState<Ticket[]>([])
  const [tickets, setTickets] = useState<{
    pendentes: Ticket[]
    emAndamento: Ticket[]
    finalizados: Ticket[]
  }>({
    pendentes: [],
    emAndamento: [],
    finalizados: [],
  })
  const [loading, setLoading] = useState(true)

  // Fetch tickets from API
  useEffect(() => {
    const fetchTickets = async () => {
      setLoading(true)
      try {
        // In a real application, replace this with your actual API endpoint
        const response = await fetch("/api/tickets")

        if (!response.ok) {
          throw new Error("Failed to fetch tickets")
        }

        const data = await response.json()

        // Process and categorize tickets
        const pendentes = data.filter((ticket) => ticket.status === "Pendente")
        const emAndamento = data.filter((ticket) => ticket.status === "Em Andamento")
        const finalizados = data.filter((ticket) => ticket.status === "Finalizado")

        setTickets({
          pendentes,
          emAndamento,
          finalizados,
        })
      } catch (error) {
        console.error("Error fetching tickets:", error)
        toast({
          variant: "destructive",
          title: "Erro ao carregar chamados",
          description: "Não foi possível carregar os chamados. Usando dados de exemplo.",
        })

        // Fallback to mock data if API fails
        setTickets({
          pendentes: [
            { id: 1, titulo: "Problema com impressora", urgencia: "Alta", data: "2023-05-15", status: "Pendente" },
            { id: 2, titulo: "Acesso ao sistema bloqueado", urgencia: "Média", data: "2023-05-16", status: "Pendente" },
            { id: 3, titulo: "Computador não liga", urgencia: "Alta", data: "2023-05-17", status: "Pendente" },
          ],
          emAndamento: [
            { id: 4, titulo: "Instalação de software", urgencia: "Baixa", data: "2023-05-14", status: "Em Andamento" },
            { id: 5, titulo: "Configuração de email", urgencia: "Média", data: "2023-05-13", status: "Em Andamento" },
          ],
          finalizados: [
            { id: 6, titulo: "Troca de teclado", urgencia: "Baixa", data: "2023-05-10", status: "Finalizado" },
            { id: 7, titulo: "Atualização de sistema", urgencia: "Média", data: "2023-05-09", status: "Finalizado" },
            { id: 8, titulo: "Recuperação de arquivos", urgencia: "Alta", data: "2023-05-08", status: "Finalizado" },
            { id: 9, titulo: "Configuração de VPN", urgencia: "Média", data: "2023-05-07", status: "Finalizado" },
          ],
        })
      } finally {
        setLoading(false)
      }
    }

    fetchTickets()
  }, [toast])

  useEffect(() => {
    // Check if user is logged in
    const user = localStorage.getItem("user")
    if (!user) {
      router.push("/")
    }
  }, [router])

  useEffect(() => {
    if (selectedStatus === "pendentes") {
      setTicketsToShow(tickets.pendentes)
    } else if (selectedStatus === "emAndamento") {
      setTicketsToShow(tickets.emAndamento)
    } else if (selectedStatus === "finalizados") {
      setTicketsToShow(tickets.finalizados)
    } else {
      setTicketsToShow([])
    }
  }, [selectedStatus, tickets])

  const handleCreateTicket = () => {
    router.push("/criar-chamado")
  }

  // Prepare chart data for the single status chart
  const statusChartData = [
    {
      name: "Pendentes",
      quantidade: tickets.pendentes.length,
      fill: COLORS.danger,
    },
    {
      name: "Em Andamento",
      quantidade: tickets.emAndamento.length,
      fill: COLORS.primary,
    },
    {
      name: "Finalizados",
      quantidade: tickets.finalizados.length,
      fill: COLORS.success,
    },
  ]

  // Custom tooltip for BarChart
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border rounded shadow-md">
          <p className="font-medium">{`${label}: ${payload[0].value} chamados`}</p>
        </div>
      )
    }
    return null
  }

  return (
    <>
      <Navigation />
      <div className="container mx-auto pt-20 px-4 pb-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold" style={{ color: COLORS.secondary }}>
            Dashboard
          </h1>
          <Button onClick={handleCreateTicket} style={{ backgroundColor: COLORS.primary, color: "white" }}>
            Abrir Chamado
          </Button>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div
              className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2"
              style={{ borderColor: COLORS.primary }}
            ></div>
          </div>
        ) : (
          <>
            <Card className="shadow-lg border-0 mb-8">
              <CardHeader style={{ backgroundColor: COLORS.secondary, color: "white" }} className="rounded-t-lg">
                <CardTitle>Status dos Chamados</CardTitle>
                <CardDescription className="text-gray-200">Distribuição de chamados por status</CardDescription>
              </CardHeader>
              <CardContent className="h-[400px] pt-6">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={statusChartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fill: COLORS.secondary, fontSize: 14 }} tickLine={false} />
                    <YAxis
                      tick={{ fill: COLORS.secondary }}
                      axisLine={false}
                      tickLine={false}
                      label={{
                        value: "Quantidade",
                        angle: -90,
                        position: "insideLeft",
                        style: { fill: COLORS.secondary },
                      }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend verticalAlign="top" height={36} />
                    <Bar dataKey="quantidade" name="Quantidade de Chamados" radius={[8, 8, 0, 0]} barSize={80}>
                      {statusChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <Card
                className={`cursor-pointer hover:shadow-lg transition-shadow ${
                  selectedStatus === "pendentes" ? "ring-2" : ""
                }`}
                style={{
                  borderColor: COLORS.danger,
                  ...(selectedStatus === "pendentes" ? { ringColor: COLORS.danger } : {}),
                }}
                onClick={() => setSelectedStatus(selectedStatus === "pendentes" ? null : "pendentes")}
              >
                <CardHeader style={{ backgroundColor: `${COLORS.danger}20` }}>
                  <CardTitle className="flex justify-between">
                    <span style={{ color: COLORS.secondary }}>Pendentes</span>
                    <span
                      className="text-white rounded-full w-8 h-8 flex items-center justify-center"
                      style={{ backgroundColor: COLORS.danger }}
                    >
                      {tickets.pendentes.length}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <p className="text-gray-600">Chamados aguardando atendimento</p>
                </CardContent>
              </Card>

              <Card
                className={`cursor-pointer hover:shadow-lg transition-shadow ${
                  selectedStatus === "emAndamento" ? "ring-2" : ""
                }`}
                style={{
                  borderColor: COLORS.primary,
                  ...(selectedStatus === "emAndamento" ? { ringColor: COLORS.primary } : {}),
                }}
                onClick={() => setSelectedStatus(selectedStatus === "emAndamento" ? null : "emAndamento")}
              >
                <CardHeader style={{ backgroundColor: `${COLORS.primary}20` }}>
                  <CardTitle className="flex justify-between">
                    <span style={{ color: COLORS.secondary }}>Em Andamento</span>
                    <span
                      className="text-white rounded-full w-8 h-8 flex items-center justify-center"
                      style={{ backgroundColor: COLORS.primary }}
                    >
                      {tickets.emAndamento.length}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <p className="text-gray-600">Chamados em processo de atendimento</p>
                </CardContent>
              </Card>

              <Card
                className={`cursor-pointer hover:shadow-lg transition-shadow ${
                  selectedStatus === "finalizados" ? "ring-2" : ""
                }`}
                style={{
                  borderColor: COLORS.success,
                  ...(selectedStatus === "finalizados" ? { ringColor: COLORS.success } : {}),
                }}
                onClick={() => setSelectedStatus(selectedStatus === "finalizados" ? null : "finalizados")}
              >
                <CardHeader style={{ backgroundColor: `${COLORS.success}20` }}>
                  <CardTitle className="flex justify-between">
                    <span style={{ color: COLORS.secondary }}>Finalizados</span>
                    <span
                      className="text-white rounded-full w-8 h-8 flex items-center justify-center"
                      style={{ backgroundColor: COLORS.success }}
                    >
                      {tickets.finalizados.length}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <p className="text-gray-600">Chamados concluídos</p>
                </CardContent>
              </Card>
            </div>

            {selectedStatus && (
              <Card className="shadow-lg border-0">
                <CardHeader
                  style={{
                    backgroundColor:
                      selectedStatus === "pendentes"
                        ? COLORS.danger
                        : selectedStatus === "emAndamento"
                          ? COLORS.primary
                          : COLORS.success,
                    color: "white",
                  }}
                  className="rounded-t-lg"
                >
                  <CardTitle>
                    Chamados{" "}
                    {selectedStatus === "pendentes"
                      ? "Pendentes"
                      : selectedStatus === "emAndamento"
                        ? "Em Andamento"
                        : "Finalizados"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead
                        className="text-xs uppercase"
                        style={{ backgroundColor: `${COLORS.secondary}10`, color: COLORS.secondary }}
                      >
                        <tr>
                          <th className="px-6 py-3">ID</th>
                          <th className="px-6 py-3">Título</th>
                          <th className="px-6 py-3">Urgência</th>
                          <th className="px-6 py-3">Data</th>
                          <th className="px-6 py-3">Ações</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ticketsToShow.map((ticket) => (
                          <tr key={ticket.id} className="bg-white border-b hover:bg-gray-50">
                            <td className="px-6 py-4">{ticket.id}</td>
                            <td className="px-6 py-4">{ticket.titulo}</td>
                            <td className="px-6 py-4">
                              <span
                                className={`px-2 py-1 rounded text-xs font-medium text-white`}
                                style={{
                                  backgroundColor:
                                    ticket.urgencia === "Alta"
                                      ? COLORS.danger
                                      : ticket.urgencia === "Média"
                                        ? COLORS.warning
                                        : COLORS.success,
                                }}
                              >
                                {ticket.urgencia}
                              </span>
                            </td>
                            <td className="px-6 py-4">{ticket.data}</td>
                            <td className="px-6 py-4">
                              <Button
                                variant="outline"
                                size="sm"
                                style={{ borderColor: COLORS.primary, color: COLORS.primary }}
                              >
                                Ver Detalhes
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </>
  )
}
