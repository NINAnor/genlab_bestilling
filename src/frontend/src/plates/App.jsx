import { useEffect } from 'react';
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast';
import PlateGrid from './components/PlateGrid';
import usePlateStore from './store';
import { config } from './config';

const queryClient = new QueryClient()

function App() {
  const init = usePlateStore((s) => s.init);

  useEffect(() => {
    init(config);
  }, [init]);

  return (
    <QueryClientProvider client={queryClient}>
      <h2 className='text-4xl font-bold mb-5'>Plates</h2>
      <Toaster />
      <div className='p-4 bg-white mb-2 rounded'>
        <PlateGrid />
      </div>
    </QueryClientProvider>
  )
}

export default App
