import { Link, useLocation } from 'react-router-dom'
import { 
  Database, 
  Play, 
  BarChart3, 
  Eye,
  Home,
  Menu
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useState } from 'react'

const navigationItems = [
  {
    name: 'Datasets',
    href: '/datasets',
    icon: Database,
    description: 'Manage and explore datasets'
  },
  {
    name: 'Jobs',
    href: '/jobs',
    icon: Play,
    description: 'Processing jobs and queue'
  },
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: BarChart3,
    description: 'Statistics and analytics'
  },
  {
    name: 'Review',
    href: '/review',
    icon: Eye,
    description: 'Scene review and annotation'
  }
]

export function Navigation() {
  const location = useLocation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  return (
    <>
      {/* Desktop Navigation */}
      <nav className="hidden md:flex border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center">
          <div className="mr-4 flex">
            <Link to="/" className="mr-6 flex items-center space-x-2">
              <Home className="h-6 w-6" />
              <span className="hidden font-bold sm:inline-block">
                Modomo Dataset Management
              </span>
            </Link>
            <nav className="flex items-center space-x-6 text-sm font-medium">
              {navigationItems.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    className={cn(
                      "flex items-center space-x-2 transition-colors hover:text-foreground/80",
                      isActive ? "text-foreground" : "text-foreground/60"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </nav>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation */}
      <nav className="md:hidden border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center justify-between">
          <Link to="/" className="flex items-center space-x-2">
            <Home className="h-6 w-6" />
            <span className="font-bold">MDM</span>
          </Link>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="px-3"
          >
            <Menu className="h-4 w-4" />
          </Button>
        </div>
        
        {/* Mobile Menu Dropdown */}
        {isMobileMenuOpen && (
          <div className="border-t bg-background p-4">
            <div className="grid gap-2">
              {navigationItems.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={cn(
                      "flex items-center space-x-3 rounded-md p-3 text-sm transition-colors hover:bg-accent hover:text-accent-foreground",
                      isActive && "bg-accent text-accent-foreground"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <div className="flex flex-col">
                      <span className="font-medium">{item.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {item.description}
                      </span>
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>
        )}
      </nav>
    </>
  )
}