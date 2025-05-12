import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [items, setItems] = useState([])
  const [newItem, setNewItem] = useState({ name: '', description: '' })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchItems()
  }, [])

  const fetchItems = async () => {
    try {
      setLoading(true)
      const response = await axios.get('http://localhost:8000/api/items')
      setItems(response.data)
      setError(null)
    } catch (err) {
      setError('Error fetching items. Is the backend server running?')
      console.error('Error fetching items:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setNewItem({ ...newItem, [name]: value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!newItem.name) return

    try {
      const response = await axios.post('http://localhost:8000/api/items', {
        ...newItem,
        id: items.length + 1,
        completed: false
      })
      setItems([...items, response.data])
      setNewItem({ name: '', description: '' })
    } catch (err) {
      setError('Error adding item')
      console.error('Error adding item:', err)
    }
  }

  const toggleComplete = async (id) => {
    try {
      const item = items.find(item => item.id === id)
      const updatedItem = { ...item, completed: !item.completed }

      await axios.put(`http://localhost:8000/api/items/${id}`, updatedItem)

      setItems(items.map(item =>
        item.id === id ? { ...item, completed: !item.completed } : item
      ))
    } catch (err) {
      setError('Error updating item')
      console.error('Error updating item:', err)
    }
  }

  const deleteItem = async (id) => {
    try {
      await axios.delete(`http://localhost:8000/api/items/${id}`)
      setItems(items.filter(item => item.id !== id))
    } catch (err) {
      setError('Error deleting item')
      console.error('Error deleting item:', err)
    }
  }

  return (
    <div className="app-container">
      <h1>Todo App</h1>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit} className="add-form">
        <input
          type="text"
          name="name"
          placeholder="Task name"
          value={newItem.name}
          onChange={handleInputChange}
          required
        />
        <input
          type="text"
          name="description"
          placeholder="Description (optional)"
          value={newItem.description}
          onChange={handleInputChange}
        />
        <button type="submit">Add Task</button>
      </form>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <ul className="todo-list">
          {items.length === 0 ? (
            <p>No tasks yet. Add one above!</p>
          ) : (
            items.map(item => (
              <li key={item.id} className={item.completed ? 'completed' : ''}>
                <div className="todo-info">
                  <h3>{item.name}</h3>
                  {item.description && <p>{item.description}</p>}
                </div>
                <div className="todo-actions">
                  <button onClick={() => toggleComplete(item.id)}>
                    {item.completed ? 'Undo' : 'Complete'}
                  </button>
                  <button onClick={() => deleteItem(item.id)} className="delete-btn">
                    Delete
                  </button>
                </div>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  )
}

export default App
