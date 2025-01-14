import { useState } from "react";
import Table from "./SampleMarkerTable";


export default function OrderMarker() {
    const [selection, setSelection] = useState({});
    return (
        <Table setRowSelection={setSelection} rowSelection={selection} />
    )
}
