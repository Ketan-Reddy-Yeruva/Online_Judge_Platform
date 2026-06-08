import { useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';

function App() {
  const [code, setCode] = useState('#include <iostream>\nusing namespace std;\n\nint main() {\n    int a, b;\n    if(cin >> a >> b) {\n        cout << a + b;\n    }\n    return 0;\n}');
  const [verdict, setVerdict] = useState('Waiting for submission...');
  const [isLoading, setIsLoading] = useState(false);

  const handleEditorChange = (value) => {
    setCode(value);
  };

  const submitCode = async () => {
    setIsLoading(true);
    setVerdict('Judging... ⏳');
    
    try {
      // Send the code to your Python backend
      const response = await axios.post('http://127.0.0.1:8000/submit', {
        problem_id: 1,
        source_code: code,
        input_data: "10 15",
        expected_output: "25"
      });
      
      setVerdict(response.data.verdict);
    } catch (error) {
      console.error(error);
      setVerdict('Error: Could not connect to the server ❌');
    }
    
    setIsLoading(false);
  };

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif' }}>
      
      {/* LEFT SIDE: Problem Description */}
      <div style={{ flex: 1, padding: '40px', backgroundColor: '#f8f9fa', overflowY: 'auto' }}>
        <h1 style={{ margin: '0 0 10px 0' }}>Problem 1: A + B</h1>
        <hr style={{ border: '1px solid #ddd', marginBottom: '20px' }} />
        
        <p>Write a program that adds two integers and prints the result.</p>
        
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
        <Editor
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

export default App;