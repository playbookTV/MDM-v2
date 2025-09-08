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
        data-oid="65peida"
      >
        <div className="container flex h-14 items-center" data-oid="wwrmy08">
          <div className="mr-4 flex" data-oid="2:po_na">
            <Link
              to="/"
              className="mr-6 flex items-center space-x-2"
              data-oid="fr:al1n"
            >
              <Home className="h-6 w-6" data-oid="xzb54e4" />
              <span
                className="hidden font-bold sm:inline-block"
                data-oid="e5am.ie"
              >
                Modomo Dataset Management
              </span>
            </Link>
            <nav
              className="flex items-center space-x-6 text-sm font-medium"
              data-oid="wmcjmi-"
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
                    data-oid="oozcght"
                  >
                    <Icon className="h-4 w-4" data-oid="ml.ryw2" />
                    <span data-oid="odom52q">{item.name}</span>
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
        data-oid="mitdu5b"
      >
        <div
          className="container flex h-14 items-center justify-between"
          data-oid="14a8h59"
        >
          <Link
            to="/"
            className="flex items-center space-x-2"
            data-oid="62tzagh"
          >
            <Home className="h-6 w-6" data-oid="x5_8vta" />
            <span className="font-bold" data-oid="6lydiqe">
              MDM
            </span>
          </Link>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="px-3"
            data-oid="ds5ilos"
          >
            <Menu className="h-4 w-4" data-oid="dcr3omd" />
          </Button>
        </div>

        {/* Mobile Menu Dropdown */}
        {isMobileMenuOpen && (
          <div className="border-t bg-background p-4" data-oid="-bldn55">
            <div className="grid gap-2" data-oid="9.--6bb">
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
                    data-oid="nakziyc"
                  >
                    <Icon className="h-4 w-4" data-oid="k12pnya" />
                    <div className="flex flex-col" data-oid="15f73-o">
                      <span className="font-medium" data-oid="uvww.h9">
                        {item.name}
                      </span>
                      <span
                        className="text-xs text-muted-foreground"
                        data-oid="c742lh:"
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
