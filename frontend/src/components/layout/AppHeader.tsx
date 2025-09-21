"use client";

import { useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { 
  LayoutDashboard, 
  Plus, 
  Settings, 
  User, 
  Menu,
  ChevronDown
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface AppHeaderProps {
  onSidebarToggle?: () => void;
  sidebarCollapsed?: boolean;
}

export function AppHeader({ onSidebarToggle, sidebarCollapsed }: AppHeaderProps) {
  const [currentProject] = useState("IMU Analysis Session");
  const router = useRouter();
  const pathname = usePathname();

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4 sticky top-0 z-50">
      {/* Left Section - Logo and Navigation */}
      <div className="flex items-center space-x-4">
        {/* Sidebar Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onSidebarToggle}
          className="lg:hidden"
        >
          <Menu className="w-4 h-4" />
        </Button>

        {/* Logo */}
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-[#C41230] rounded flex items-center justify-center">
            <span className="text-white font-bold text-sm">MBL</span>
          </div>
          <span className="font-semibold text-gray-900 hidden sm:block">IMUViz</span>
        </div>

        {/* Navigation */}
        <nav className="hidden md:flex items-center space-x-1">
          <Button
            variant={pathname === '/dashboard' ? 'default' : 'ghost'}
            size="sm"
            className={`flex items-center space-x-2 ${
              pathname === '/dashboard' 
                ? 'bg-[#C41230] text-white hover:bg-[#A00E26]' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
            onClick={() => router.push('/dashboard')}
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Dashboard</span>
          </Button>
          
          <Button
            variant={pathname === '/' ? 'default' : 'ghost'}
            size="sm"
            className={`flex items-center space-x-2 ${
              pathname === '/' 
                ? 'bg-[#C41230] text-white hover:bg-[#A00E26]' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
            onClick={() => router.push('/')}
          >
            <Plus className="w-4 h-4" />
            <span>New Session</span>
          </Button>
        </nav>
      </div>

      {/* Center Section - Current Project */}
      <div className="flex-1 flex justify-center">
        <div className="flex items-center space-x-2 bg-gray-50 px-3 py-1.5 rounded-md">
          <span className="text-sm text-gray-600">Current:</span>
          <span className="text-sm font-medium text-gray-900">{currentProject}</span>
        </div>
      </div>

      {/* Right Section - User Menu */}
      <div className="flex items-center space-x-3">
        {/* Settings */}
        <Button variant="ghost" size="sm" className="hidden sm:flex">
          <Settings className="w-4 h-4" />
        </Button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="flex items-center space-x-2">
              <div className="w-7 h-7 bg-gray-300 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-gray-600" />
              </div>
              <ChevronDown className="w-3 h-3 text-gray-500 hidden sm:block" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuItem>
              <User className="w-4 h-4 mr-2" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => router.push('/dashboard')}>
              <LayoutDashboard className="w-4 h-4 mr-2" />
              Dashboard
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push('/')}>
              <Plus className="w-4 h-4 mr-2" />
              New Session
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-600">
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}