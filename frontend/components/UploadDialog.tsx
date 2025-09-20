'use client'
import { useState } from 'react'

export default function UploadDialog(){
  const [file, setFile] = useState<File|null>(null)
  const [name, setName] = useState('Proyecto Demo')
  const upload = async (endpoint: 'excel') => {
    if(!file) return
    const fd = new FormData()
    fd.append('project_name', name)
    fd.append('file', file)
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/v1/imports/${endpoint}`, { method:'POST', body:fd })
    const data = await res.json()
    alert(JSON.stringify(data))
  }
  return (
    <div style={{display:'flex', gap:10, alignItems:'center'}}>
      <input value={name} onChange={e=>setName(e.target.value)} placeholder='Nombre del proyecto' />
      <input type='file' onChange={e=>setFile(e.target.files?.[0]||null)} />
      <button onClick={()=>upload('excel')}>Importar Excel</button>
    </div>
  )
}
