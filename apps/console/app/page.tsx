"use client";
import { useState } from "react";
export default function Home(){
  const [resp,setResp]=useState<any>(null);
  async function runPlan(){
    const r=await fetch("/api/adk/v1/runs/plan",{method:"POST",headers:{"content-type":"application/json"},
      body:JSON.stringify({pr:{repo:"owner/repo",pr_number:1,branch:"feature",head_sha:"deadbeef"},mode:"plan",labels:[],extra:{message:"hello"}})});
    setResp(await r.json());
  }
  return (<div style={{padding:16}}>
    <h1>Kyros Agent Console</h1>
    <button onClick={runPlan}>Run Plan</button>
    <pre>{JSON.stringify(resp,null,2)}</pre>
  </div>);
}