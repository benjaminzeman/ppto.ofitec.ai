import UploadDialog from '../../components/UploadDialog'
export default function BudgetsPage(){
  return (
    <div style={{display:'flex', flexDirection:'column', gap:20}}>
      <h1>Presupuestos</h1>
      <UploadDialog />
    </div>
  )
}
