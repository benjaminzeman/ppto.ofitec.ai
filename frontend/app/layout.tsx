export const metadata = { title: 'OFITEC', description: 'Presupuestos & Mediciones' }
export default function RootLayout({children}:{children:React.ReactNode}){
  return (
    <html lang="es">
      <body style={{fontFamily:'sans-serif', margin:0}}>
        <header style={{padding:'10px 20px', background:'#111', color:'#fff'}}>OFITEC</header>
        <main style={{padding:'20px'}}>{children}</main>
      </body>
    </html>
  )
}
