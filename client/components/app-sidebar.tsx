"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bookmark,
  ChevronsUpDown,
  CircleHelp,
  History,
  Languages,
  LogOut,
  Sparkles,
  Video,
  type LucideIcon,
} from "lucide-react";

import { Logo } from "./logo";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

type NavItem = { title: string; url: string; icon: LucideIcon };

const mainNav: NavItem[] = [
  { title: "Create", url: "/dashboard", icon: Sparkles },
  { title: "Dubbing", url: "/translate", icon: Languages },
  { title: "History", url: "/dashboard/history", icon: History },
];

const libraryNav: NavItem[] = [
  { title: "Recent videos", url: "/dashboard/history", icon: Video },
  { title: "Saved clips", url: "#", icon: Bookmark },
];

export function AppSidebar({
  user,
  ...props
}: React.ComponentProps<typeof Sidebar> & {
  user: { name: string; email: string; avatar: string };
}) {
  const pathname = usePathname();
  const isActive = (url: string) =>
    url !== "#" && (pathname === url || (url !== "/dashboard" && pathname.startsWith(url)));

  const initials = user.name
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <Sidebar {...props}>
      <SidebarHeader>
        <div className="flex items-center gap-3 px-1.5 py-1">
          <Logo size={34} />
          <div className="grid leading-none">
            <span className="font-display text-lg font-bold tracking-tight text-foreground">
              Moment
            </span>
            <span className="label-mono mt-1 text-[10px] text-muted-foreground">
              Shorts studio
            </span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className="gap-1">
        <SidebarGroup>
          <SidebarMenu>
            {mainNav.map((item) => (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton asChild isActive={isActive(item.url)} tooltip={item.title}>
                  <Link href={item.url}>
                    <item.icon />
                    <span>{item.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel className="label-mono text-[11px]">Library</SidebarGroupLabel>
          <SidebarMenu>
            {libraryNav.map((item) => (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton asChild tooltip={item.title}>
                  <Link href={item.url}>
                    <item.icon />
                    <span>{item.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="gap-2">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild tooltip="Help & support">
              <a href="#">
                <CircleHelp />
                <span>Help &amp; support</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-3 rounded-xl border border-sidebar-border bg-card/60 p-2.5 text-left transition-colors hover:bg-sidebar-accent/40">
              <div className="flex size-9 flex-none items-center justify-center rounded-[10px] bg-sidebar-accent font-semibold text-sidebar-accent-foreground">
                {initials || "U"}
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-[13px] font-semibold text-foreground">
                  {user.name}
                </div>
                <div className="label-mono truncate text-[11px] normal-case tracking-normal text-muted-foreground">
                  {user.email}
                </div>
              </div>
              <ChevronsUpDown className="size-4 text-muted-foreground" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            side="top"
            align="start"
            className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-xl"
          >
            <DropdownMenuItem>
              <Sparkles />
              Upgrade plan
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/logout">
                <LogOut />
                Log out
              </Link>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
