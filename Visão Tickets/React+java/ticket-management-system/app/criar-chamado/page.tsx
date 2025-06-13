"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Navigation } from "@/components/navigation"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { TagInput } from "@/components/tag-input"

export default function CriarChamado() {
  const router = useRouter()
  const { toast } = useToast()
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Form fields
  const [tipo, setTipo] = useState("")
  const [categoria, setCategoria] = useState("")
  const [urgencia, setUrgencia] = useState("Média")
  const [observadores, setObservadores] = useState([])
  const [titulo, setTitulo] = useState("")
  const [descricao, setDescricao] = useState("")
  const [setor, setSetor] = useState("")

  // Mock data for dropdowns
  const tipos = ["Incidente", "Requisição"]
  const categorias = [
    { id: 1, nome: "Hardware" },
    { id: 2, nome: "Software" },
    { id: 3, nome: "Rede" },
    { id: 4, nome: "Acesso" },
    { id: 5, nome: "Outros" },
  ]
  const urgencias = ["Baixa", "Média", "Alta"]
  const setores = [
    { id: 1, nome: "TI" },
    { id: 2, nome: "RH" },
    { id: 3, nome: "Financeiro" },
    { id: 4, nome: "Comercial" },
    { id: 5, nome: "Operações" },
  ]
  const observadoresLista = [
    { value: "joao.silva", name: "João Silva" },
    { value: "maria.santos", name: "Maria Santos" },
    { value: "pedro.oliveira", name: "Pedro Oliveira" },
    { value: "ana.costa", name: "Ana Costa" },
    { value: "carlos.ferreira", name: "Carlos Ferreira" },
  ]

  useEffect(() => {
    // Check if user is logged in
    const user = localStorage.getItem("user")
    if (!user) {
      router.push("/")
    }
  }, [router])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)

    // Validate required fields
    if (!tipo || !titulo || !descricao || !setor) {
      toast({
        variant: "destructive",
        title: "Erro ao criar chamado",
        description: "Preencha todos os campos obrigatórios",
      })
      setIsSubmitting(false)
      return
    }

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500))

      toast({
        title: "Chamado criado com sucesso!",
        description: "Seu chamado foi registrado no sistema",
      })

      router.push("/dashboard")
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Erro ao criar chamado",
        description: "Ocorreu um erro ao tentar criar o chamado",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <>
      <Navigation />
      <div className="container mx-auto pt-20 px-4 pb-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Criar Novo Chamado</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="tipo">
                    Tipo <span className="text-red-500">*</span>
                  </Label>
                  <Select value={tipo} onValueChange={setTipo} required>
                    <SelectTrigger id="tipo">
                      <SelectValue placeholder="Selecione o tipo" />
                    </SelectTrigger>
                    <SelectContent>
                      {tipos.map((t) => (
                        <SelectItem key={t} value={t}>
                          {t}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="categoria">Categoria</Label>
                  <Select value={categoria} onValueChange={setCategoria}>
                    <SelectTrigger id="categoria">
                      <SelectValue placeholder="Selecione a categoria" />
                    </SelectTrigger>
                    <SelectContent>
                      {categorias.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id.toString()}>
                          {cat.nome}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="urgencia">Urgência</Label>
                  <Select value={urgencia} onValueChange={setUrgencia}>
                    <SelectTrigger id="urgencia">
                      <SelectValue placeholder="Selecione a urgência" />
                    </SelectTrigger>
                    <SelectContent>
                      {urgencias.map((urg) => (
                        <SelectItem key={urg} value={urg}>
                          {urg}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="setor">
                    Setor Solicitante <span className="text-red-500">*</span>
                  </Label>
                  <Select value={setor} onValueChange={setSetor} required>
                    <SelectTrigger id="setor">
                      <SelectValue placeholder="Selecione o setor" />
                    </SelectTrigger>
                    <SelectContent>
                      {setores.map((s) => (
                        <SelectItem key={s.id} value={s.id.toString()}>
                          {s.nome}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="observadores">Observadores</Label>
                <TagInput
                  id="observadores"
                  placeholder="Digite para buscar e selecionar observadores..."
                  tags={observadores}
                  setTags={setObservadores}
                  suggestions={observadoresLista}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="titulo">
                  Título do Chamado <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="titulo"
                  value={titulo}
                  onChange={(e) => setTitulo(e.target.value)}
                  placeholder="Digite o título do chamado"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="descricao">
                  Descrição <span className="text-red-500">*</span>
                </Label>
                <Textarea
                  id="descricao"
                  value={descricao}
                  onChange={(e) => setDescricao(e.target.value)}
                  placeholder="Digite a descrição detalhada do chamado"
                  rows={6}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="arquivo">Arquivo(s) (40 MB máx)</Label>
                <Input id="arquivo" type="file" multiple />
              </div>

              <div className="flex justify-between">
                <Button type="button" variant="outline" onClick={() => router.push("/dashboard")}>
                  Voltar
                </Button>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "Criando..." : "Criar Chamado"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </>
  )
}
