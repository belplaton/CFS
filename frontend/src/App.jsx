import { useState } from 'react'
import { Cloud, Upload, Folder, HardDrive } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="border-b bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cloud className="h-8 w-8 text-primary" />
            <h1 className="text-xl font-bold">Cloud File Storage</h1>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost">Войти</Button>
            <Button>Регистрация</Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <section className="text-center py-12">
          <h2 className="text-4xl font-bold mb-4">
            Ваше личное облачное хранилище
          </h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Безопасное хранение файлов, синхронизация между устройствами и общий доступ к вашим данным
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" className="gap-2">
              <Upload className="h-4 w-4" />
              Начать бесплатно
            </Button>
            <Button size="lg" variant="outline">
              Узнать больше
            </Button>
          </div>
        </section>

        {/* Features */}
        <section className="grid md:grid-cols-3 gap-6 py-12">
          <Card>
            <CardHeader>
              <Folder className="h-12 w-12 text-primary mb-2" />
              <CardTitle>Управление файлами</CardTitle>
              <CardDescription>
                Загрузка, скачивание, организация файлов по папкам
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Интуитивный интерфейс для работы с вашими файлами
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <HardDrive className="h-12 w-12 text-primary mb-2" />
              <CardTitle>5 ГБ бесплатно</CardTitle>
              <CardDescription>
                Базовый тариф с возможностью расширения до 100 ГБ
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Премиум подписка для больших объёмов данных
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Cloud className="h-12 w-12 text-primary mb-2" />
              <CardTitle>Безопасность</CardTitle>
              <CardDescription>
                Двухфакторная аутентификация и шифрование данных
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Ваши данные под надёжной защитой
              </p>
            </CardContent>
          </Card>
        </section>

        {/* Test Section */}
        <section className="py-8">
          <Card>
            <CardHeader>
              <CardTitle>Тестовая секция</CardTitle>
              <CardDescription>
                Проверка работы React + shadcn/ui
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-4">
              <p className="text-sm">Счётчик: {count}</p>
              <Button onClick={() => setCount((prev) => prev + 1)}>
                Увеличить
              </Button>
            </CardContent>
          </Card>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t bg-gray-50 dark:bg-gray-900 py-6 mt-12">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          © 2026 Cloud File Storage. Все права защищены.
        </div>
      </footer>
    </div>
  )
}

export default App
