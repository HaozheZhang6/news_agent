'use client'

import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'

type Props = { onClose: () => void }

const AVAILABLE_TOPICS = [
  'technology',
  'finance',
  'politics',
  'crypto',
  'energy',
  'healthcare',
  'automotive',
  'real_estate',
  'retail',
  'general'
]

export default function UserProfileModal({ onClose }: Props) {
  const userId = process.env.NEXT_PUBLIC_DEMO_USER_ID || '03f6b167-0c4d-4983-a380-54b8eb42f830'
  const apiBase = process.env.NEXT_PUBLIC_API_URL

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [preferredTopics, setPreferredTopics] = useState<string[]>([])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${apiBase}/api/user/preferences?user_id=${encodeURIComponent(userId)}`)
        if (!res.ok) throw new Error('Failed to fetch preferences')
        const data = await res.json()
        setPreferredTopics(data.preferred_topics || [])
      } catch (e) {
        toast.error('Failed to load user preferences')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [apiBase, userId])

  const toggleTopic = (topic: string) => {
    setPreferredTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    )
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const res = await fetch(`${apiBase}/api/user/preferences?user_id=${encodeURIComponent(userId)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preferred_topics: preferredTopics })
      })
      if (!res.ok) throw new Error('Failed to save')
      toast.success('Preferences saved')
      onClose()
    } catch (e) {
      toast.error('Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Edit Interests</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>

        {loading ? (
          <div className="text-sm text-gray-600 dark:text-gray-300">Loading...</div>
        ) : (
          <div className="grid grid-cols-2 gap-2">
            {AVAILABLE_TOPICS.map((topic) => {
              const active = preferredTopics.includes(topic)
              return (
                <button
                  key={topic}
                  onClick={() => toggleTopic(topic)}
                  className={`text-sm px-3 py-2 rounded border transition-colors ${
                    active
                      ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-400 text-blue-700 dark:text-blue-200'
                      : 'bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200'
                  }`}
                >
                  {topic}
                </button>
              )
            })}
          </div>
        )}

        <div className="mt-6 flex justify-end space-x-2">
          <button onClick={onClose} className="px-4 py-2 rounded bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-100">Cancel</button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}


