import React from 'react'
import ReactDOM from 'react-dom/client'
import FloatingBookingAgent from './BookingAgent.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <FloatingBookingAgent businessId="demo" />
  </React.StrictMode>,
)