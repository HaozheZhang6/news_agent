'use client'

import { useState } from 'react'
import { User as UserIcon } from 'lucide-react'
import UserProfileModal from '@/components/UserProfileModal'

export default function Header() {
  const [isProfileOpen, setIsProfileOpen] = useState(false)

  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center space-x-2">
        <span className="text-2xl">🎙️</span>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Voice News Agent</h1>
      </div>
      <button
        aria-label="Open profile"
        onClick={() => setIsProfileOpen(true)}
        className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
      >
        <UserIcon className="w-5 h-5 text-gray-800 dark:text-gray-100" />
      </button>
      {isProfileOpen && (
        <UserProfileModal onClose={() => setIsProfileOpen(false)} />
      )}
    </div>
  )
}


