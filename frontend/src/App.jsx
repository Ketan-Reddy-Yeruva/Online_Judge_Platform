import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Dashboard from './Dashboard';
import Editor from './Editor'; // The file we just created

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* If the URL is exactly "/", load the Dashboard */}
        <Route path="/" element={<Dashboard />} />
        
        {/* If the URL is "/problem/1", load the Editor and pass "1" as the ID */}
        <Route path="/problem/:id" element={<Editor />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;