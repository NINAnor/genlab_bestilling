import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import Table from './components/Table'
import SampleForm from './components/SampleForm'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SampleForm />
      <Table />
    </QueryClientProvider>
  )
}

export default App
