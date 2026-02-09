
export interface FlightDeal {
    airline: string;
    flightNumber: string;
    departureCity: string;
    arrivalCity: string;
    departureDate: string; // ISO String
    returnDate: string;
    price: number;
    bookingLink: string;
    score: number; // 0-100 deal score
}

// Mock database of flights
const MOCK_FLIGHTS: FlightDeal[] = [
    {
        airline: "MockAir",
        flightNumber: "MA101",
        departureCity: "NYC",
        arrivalCity: "London",
        departureDate: "2024-05-02T10:00:00Z",
        returnDate: "2024-05-09T18:00:00Z",
        price: 450,
        bookingLink: "https://example.com/book/ma101",
        score: 95
    },
    {
        airline: "GlobalWings",
        flightNumber: "GW55",
        departureCity: "Tokyo",
        arrivalCity: "San Francisco",
        departureDate: "2024-06-10T11:00:00Z",
        returnDate: "2024-06-20T22:00:00Z",
        price: 850,
        bookingLink: "https://example.com/book/gw55",
        score: 88
    },
    {
        airline: "EuroJet",
        flightNumber: "EJ20",
        departureCity: "Berlin",
        arrivalCity: "Paris",
        departureDate: "2024-04-15T08:00:00Z",
        returnDate: "2024-04-18T20:00:00Z",
        price: 99,
        bookingLink: "https://example.com/book/ej20",
        score: 98
    }
];

export async function findDeals(origin: string | null, destination: string | null, maxPrice?: number | null): Promise<FlightDeal[]> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));

    return MOCK_FLIGHTS.filter(flight => {
        let match = true;
        if (origin && !flight.departureCity.toLowerCase().includes(origin.toLowerCase())) match = false;
        if (destination && !flight.arrivalCity.toLowerCase().includes(destination.toLowerCase())) match = false;
        if (maxPrice && flight.price > maxPrice) match = false;
        return match;
    });
}
