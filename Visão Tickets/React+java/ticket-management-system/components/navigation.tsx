"use client"

import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import Link from "next/link"

export function Navigation() {
  const router = useRouter()
  const [userName, setUserName] = useState("")

  useEffect(() => {
    const user = localStorage.getItem("user")
    if (!user) {
      router.push("/")
      return
    }

    try {
      const userData = JSON.parse(user)
      setUserName(userData.name)
    } catch (error) {
      console.error("Erro ao carregar dados do usuário:", error)
      router.push("/")
    }
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem("user")
    router.push("/")
  }

  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-2.5 fixed w-full top-0 left-0 z-50">
      <div className="flex flex-wrap justify-between items-center">
        <div className="flex items-center">
          <Link href="/dashboard" className="flex items-center">
            <span className="self-center text-xl font-semibold whitespace-nowrap">Sistema de Chamados</span>
          </Link>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium">Olá, {userName}</span>
          <Button variant="outline" size="sm" onClick={handleLogout}>
            Sair
          </Button>
        </div>
      </div>
    </nav>
  )
}
