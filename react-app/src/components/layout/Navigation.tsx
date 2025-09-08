import { Link, useLocation } from "react-router-dom";
import { Database, Play, BarChart3, Eye, Home, Menu } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useState } from "react";

const navigationItems = [
  {
    name: "Datasets",
    href: "/datasets",
    icon: Database,
    description: "Manage and explore datasets",
  },
  {
    name: "Jobs",
    href: "/jobs",
    icon: Play,
    description: "Processing jobs and queue",
  },
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: BarChart3,
    description: "Statistics and analytics",
  },
  {
    name: "Review",
    href: "/review",
    icon: Eye,
    description: "Scene review and annotation",
  },
];

export function Navigation() {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <>
      {/* Desktop Navigation */}
      <nav
        className="hidden md:flex border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
        data-oid="gt-fj.y"
      >
        <div className="container flex h-14 items-center" data-oid="uy0yh_1">
          <div className="mr-4 flex" data-oid="og_mgep">
            <Link
              to="/"
              className="mr-6 flex items-center space-x-2"
              data-oid="ia8mp:a"
            >
              <Home className="h-6 w-6" data-oid="kqgfkq-" />
              <span
                className="hidden font-bold sm:inline-block"
                data-oid="y_k5osw"
              >
                Modomo Dataset Management
              </span>
            </Link>
            <nav
              className="flex items-center space-x-6 text-sm font-medium"
              data-oid="lg5f.1q"
            >
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.href;

                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    className={cn(
                      "flex items-center space-x-2 transition-colors hover:text-foreground/80",
                      isActive ? "text-foreground" : "text-foreground/60",
                    )}
                    data-oid="8ddo:69"
                  >
                    <Icon className="h-4 w-4" data-oid="4kijg6:" />
                    <span data-oid="ccmuxgt">{item.name}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation */}
      <nav
        className="md:hidden border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
        data-oid="0oczf6_"
      >
        <div
          className="container flex h-14 items-center justify-between"
          data-oid="bjd9rgv"
        >
          <Link
            to="/"
            className="flex items-center space-x-2"
            data-oid="w7f_b::"
          >
            <Home className="h-6 w-6" data-oid="evk_8c2" />
            <span className="font-bold" data-oid="7pk.iz6">
              MDM
            </span>
          </Link>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="px-3"
            data-oid="u1kquk1"
          >
            <Menu className="h-4 w-4" data-oid=":1z.p0u" />
          </Button>
        </div>

        {/* Mobile Menu Dropdown */}
        {isMobileMenuOpen && (
          <div className="border-t bg-background p-4" data-oid="u:hzg09">
            <div className="grid gap-2" data-oid="8rljmy3">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.href;

                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={cn(
                      "flex items-center space-x-3 rounded-md p-3 text-sm transition-colors hover:bg-accent hover:text-accent-foreground",
                      isActive && "bg-accent text-accent-foreground",
                    )}
                    data-oid="w9tjffi"
                  >
                    <Icon className="h-4 w-4" data-oid="_-lfiz0" />
                    <div className="flex flex-col" data-oid="s9:onpe">
                      <span className="font-medium" data-oid="m_1kn4y">
                        {item.name}
                      </span>
                      <span
                        className="text-xs text-muted-foreground"
                        data-oid="xa4ae4f"
                      >
                        {item.description}
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </nav>
    </>
  );
}
