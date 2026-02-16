interface DealProps {
    deal: {
        airline: string
        departureCity: string
        arrivalCity: string
        price: number
        reasonToBuy: string
        bookingLink: string
        score?: number
    }
}

export default function DealCard({ deal }: DealProps) {
    return (
        <div className="glass-panel p-6 rounded-2xl space-y-4 hover:bg-slate-800/50 transition-colors">
            <div className="flex justify-between items-start">
                <div>
                    <h3 className="text-xl font-bold flex items-center gap-2">
                        {deal.departureCity} <span className="text-gray-400">→</span> {deal.arrivalCity}
                    </h3>
                    <p className="text-gray-400 text-sm">{deal.airline}</p>
                </div>
                <div className="text-right">
                    <span className="text-2xl font-bold text-green-400">${deal.price}</span>
                </div>
            </div>

            <div className="bg-blue-900/20 border border-blue-500/30 p-3 rounded-lg">
                <p className="text-sm text-blue-200">
                    <span className="font-semibold text-blue-400">AI Insight:</span> {deal.reasonToBuy}
                </p>
            </div>

            <a
                href={deal.bookingLink}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-center w-full py-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors text-sm font-medium"
            >
                View Flight
            </a>
        </div>
    )
}
