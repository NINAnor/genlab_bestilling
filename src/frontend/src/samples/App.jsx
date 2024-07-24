import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast';
import Table from './components/Table'
import SampleForm from './components/SampleForm'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <h2 className='text-4xl font-bold mb-5'>Edit Samples</h2>
      <Toaster />
      <SampleForm />
      <Table />
    </QueryClientProvider>
  )
}

export default App
