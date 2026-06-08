import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

function Dashboard() {
  const [problems, setProblems] = useState([]);
  const navigate = useNavigate();

  // Fetch problems from FastAPI when the page loads
  useEffect(() => {
    const fetchProblems = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:8000/problems');
        setProblems(response.data);
      } catch (error) {
        console.error("Error fetching problems:", error);
      }
    };
    fetchProblems();
  }, []);

  return (
    <div style={{ padding: '40px', fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif', backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto', backgroundColor: 'white', padding: '30px', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
        
        <h1 style={{ textAlign: 'center', marginBottom: '30px', color: '#333' }}>Platform Problemset</h1>
        
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#e9ecef', textAlign: 'left' }}>
              <th style={{ padding: '15px', borderBottom: '2px solid #dee2e6' }}>ID</th>
              <th style={{ padding: '15px', borderBottom: '2px solid #dee2e6' }}>Title</th>
              <th style={{ padding: '15px', borderBottom: '2px solid #dee2e6' }}>Time Limit</th>
              <th style={{ padding: '15px', borderBottom: '2px solid #dee2e6', textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {problems.map((prob) => (
              <tr key={prob.id} style={{ borderBottom: '1px solid #dee2e6' }}>
                <td style={{ padding: '15px' }}>{prob.id}</td>
                <td style={{ padding: '15px', fontWeight: 'bold' }}>{prob.title}</td>
                <td style={{ padding: '15px' }}>{prob.time_limit}s</td>
                <td style={{ padding: '15px', textAlign: 'right' }}>
                  <button 
                    onClick={() => navigate(`/problem/${prob.id}`)}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#007bff',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontWeight: 'bold'
                    }}
                  >
                    Solve
                  </button>
                </td>
              </tr>
            ))}
            {problems.length === 0 && (
              <tr>
                <td colSpan="4" style={{ padding: '20px', textAlign: 'center', color: '#6c757d' }}>
                  No problems found. Did you add them to the database?
                </td>
              </tr>
            )}
          </tbody>
        </table>
        
      </div>
    </div>
  );
}

export default Dashboard;