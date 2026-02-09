'use client'

import { createSubscription } from '@/app/actions'
import { useFormStatus } from 'react-dom'

function SubmitButton() {
    const { pending } = useFormStatus()

    return (
        <button
            type="submit"
            disabled={pending}
            className="btn-primary w-full sm:w-auto min-w-[150px] relative overflow-hidden"
        >
            {pending ? (
                <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    Analyze...
                </span>
            ) : (
                'Find Deals'
            )}
        </button>
    )
}

export default function SubscriptionForm() {
    async function handleSubmit(formData: FormData) {
        await createSubscription(formData)
    }

    return (
        <form action={handleSubmit} className="w-full max-w-2xl mx-auto space-y-4">
            <div className="relative group">
                <textarea
                    name="prompt"
                    placeholder="e.g. I want to go to Japan in April for under $800, looking for a direct flight if possible."
                    className="glass-input w-full p-4 rounded-xl min-h-[120px] text-lg resize-none"
                    required
                />
                <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 opacity-0 group-hover:opacity-10 transition-opacity pointer-events-none" />
            </div>

            <div className="flex justify-end">
                <SubmitButton />
            </div>
        </form>
    )
}
