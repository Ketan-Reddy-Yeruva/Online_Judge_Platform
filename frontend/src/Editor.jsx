import { useState, useEffect } from 'react';
import EditorComponent from '@monaco-editor/react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

function Editor() {
  const { id } = useParams();
  const navigate = useNavigate();

  // 1. New state variable to hold the dynamic problem data
  const [problemData, setProblemData] = useState(null);

  const [code, setCode] = useState('#include <iostream>\nusing namespace std;\n\nint main() {\n    // Write your code here\n    return 0;\n}');
  const [verdict, setVerdict] = useState('Waiting for submission...');
  const [isLoading, setIsLoading] = useState(false);

  // 2. Fetch the problem details from FastAPI when the page loads
  useEffect(() => {
    const fetchProblem = async () => {
      try {
        const response = await axios.get(`http://127.0.0.1:8000/problems/${id}`);
        setProblemData(response.data);
      } catch (error) {
        console.error("Error fetching problem:", error);
        setVerdict("Error: Problem not found!");
      }
    };
    fetchProblem();
  }, [id]);

  const handleEditorChange = (value) => {
    setCode(value);
  };

  const submitCode = async () => {
    setIsLoading(true);
    setVerdict('Judging... ⏳');
    
    try {
      const response = await axios.post('http://127.0.0.1:8000/submit', {
        problem_id: id,
        source_code: code,
        input_data: "10 15", // In a future update, we will pull this from the DB too!
        expected_output: "25"
      });
      
      setVerdict(response.data.verdict);
    } catch (error) {
      console.error(error);
      setVerdict('Error: Could not connect to the server ❌');
    }
    
    setIsLoading(false);
  };

  // 3. Show a loading screen while we wait for the database
  if (!problemData) {
    return <div style={{ padding: '40px', fontSize: '20px', fontFamily: 'Segoe UI' }}>Loading problem details from database...</div>;
  }

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif' }}>
      
      {/* LEFT SIDE: Dynamic Problem Description */}
      <div style={{ flex: 1, padding: '40px', backgroundColor: '#f8f9fa', overflowY: 'auto' }}>
        
        <button 
          onClick={() => navigate('/')}
          style={{ padding: '8px 16px', marginBottom: '20px', cursor: 'pointer', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', fontWeight: 'bold' }}
        >
          ← Back to Dashboard
        </button>

        {/* 4. Injecting the dynamic database values here! */}
        <h1 style={{ margin: '0 0 5px 0' }}>{problemData.title}</h1>
        <p style={{ color: '#6c757d', fontSize: '14px', marginBottom: '15px' }}>Time Limit: {problemData.time_limit} seconds</p>
        
        <hr style={{ border: '1px solid #ddd', marginBottom: '20px' }} />
        
        <p style={{ fontSize: '16px', lineHeight: '1.6' }}>{problemData.description}</p>
        
        {/* Keeping sample data hardcoded for this step, we'll make this dynamic later */}
        <div style={{ backgroundColor: '#e9ecef', padding: '15px', borderRadius: '5px', marginTop: '20px' }}>
          <p style={{ margin: '0 0 5px 0' }}><strong>Sample Input:</strong></p>
          <code style={{ fontSize: '16px' }}>10 15</code>
        </div>
        
        <div style={{ backgroundColor: '#e9ecef', padding: '15px', borderRadius: '5px', marginTop: '15px' }}>
          <p style={{ margin: '0 0 5px 0' }}><strong>Expected Output:</strong></p>
          <code style={{ fontSize: '16px' }}>25</code>
        </div>
        
        <button 
          onClick={submitCode} 
          disabled={isLoading}
          style={{ 
            marginTop: '30px', 
            padding: '12px 24px', 
            fontSize: '16px', 
            backgroundColor: isLoading ? '#6c757d' : '#28a745', 
            color: 'white', 
            border: 'none', 
            borderRadius: '5px',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            width: '100%'
          }}
        >
          {isLoading ? 'Executing on Server...' : 'Submit Code'}
        </button>
        
        <div style={{ 
          marginTop: '20px', 
          padding: '20px', 
          backgroundColor: '#fff', 
          border: '1px solid #dee2e6',
          borderRadius: '5px',
          fontSize: '18px',
          textAlign: 'center'
        }}>
          <strong>Status:</strong> <br/><br/> {verdict}
        </div>
      </div>
      
      {/* RIGHT SIDE: The Monaco Editor */}
      <div style={{ flex: 1 }}>
        <EditorComponent
          height="100vh"
          defaultLanguage="cpp"
          theme="vs-dark"
          value={code}
          onChange={handleEditorChange}
          options={{
            fontSize: 16,
            minimap: { enabled: false },
          }}
        />
      </div>
      
    </div>
  );
}

export default Editor;