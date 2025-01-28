import {
  keepPreviousData,
  useInfiniteQuery,
  // useMutation,
  // useQueryClient,
} from "@tanstack/react-query";
import { client } from "../config";
import {
  useReactTable,
  flexRender,
  getCoreRowModel,
  createColumnHelper,
} from "@tanstack/react-table";
import { useEffect, useRef, useCallback, useMemo, useState } from "react";

import { useVirtualizer } from "@tanstack/react-virtual";
import IndeterminateCheckbox from "./IndeterminateCheckbox";
import Filters from "./Filters";

async function getSamples({ pageParam, filters, markers }) {
  const joinMarkers = markers.map(m => 'markers=' + m.name);

  const url =
    pageParam ||
    `/api/samples/?${["order__status__not=draft", filters, ...joinMarkers]
      .filter((_) => _)
      .join("&")}`;
  const response = await client.get(url);
  return response.data;
}

const columnHelper = createColumnHelper();

export default function Table({ rowSelection, setRowSelection, markers, submitBtn }) {
  const tableContainerRef = useRef(null);
  const [filters, setFilters] = useState("");
  // const queryClient = useQueryClient();

  console.log(markers)

  const columns = useMemo(
    () => [
      {
        id: "select",
        size: 50,
        header: ({ table }) => (
          <IndeterminateCheckbox
            {...{
              checked: table.getIsAllRowsSelected(),
              indeterminate: table.getIsSomeRowsSelected(),
              onChange: table.getToggleAllRowsSelectedHandler(),
            }}
          />
        ),
        cell: ({ row }) => (
          <div className="px-1">
            <IndeterminateCheckbox
              {...{
                checked: row.getIsSelected(),
                disabled: !row.getCanSelect(),
                indeterminate: row.getIsSomeSelected(),
                onChange: row.getToggleSelectedHandler(),
              }}
            />
          </div>
        ),
      },
      columnHelper.accessor("genlab_id", {
        header: "Genlab ID",
      }),
      columnHelper.accessor("guid", {
        header: "GUID",
        size: 350,
      }),
      columnHelper.accessor("name", {
        header: "Sample Name",
        size: 350,
      }),
      columnHelper.accessor("species.name", {
        header: "Species",
      }),
      columnHelper.accessor("year", {
        header: "Year",
        size: 100,
      }),
      columnHelper.accessor("pop_id", {
        header: "Pop ID",
      }),
      columnHelper.accessor("location.name", {
        header: "Location",
      }),
      columnHelper.accessor("type.name", {
        header: "Sample Type",
      }),
      columnHelper.accessor("order", {
        header: "Order",
      }),
      columnHelper.accessor("notes", {
        header: "Notes",
      }),
    ],
    []
  );

  const { data, fetchNextPage, isFetching, isLoading } = useInfiniteQuery({
    queryKey: ["samples", filters, markers],
    queryFn: ({ pageParam }) => getSamples({ filters, pageParam, markers }),
    getNextPageParam: (lastGroup) => lastGroup.next,
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
  });

  const flatData = useMemo(
    () => data?.pages?.flatMap((page) => page.results) ?? [],
    [data]
  );

  const last = useMemo(() => {
    try {
      const lastIndex = data?.pages?.length - 1;
      return data?.pages[lastIndex];
    } catch (e) {
      console.log(e);
    }
    return null;
  }, [data]);

  const fetchMoreOnBottomReached = useCallback(
    (containerRefElement) => {
      if (containerRefElement) {
        const { scrollHeight, scrollTop, clientHeight } = containerRefElement;
        //once the user has scrolled within 500px of the bottom of the table, fetch more data if we can
        if (
          scrollHeight - scrollTop - clientHeight < 500 &&
          !isFetching &&
          last?.next
        ) {
          fetchNextPage();
        }
      }
    },
    [fetchNextPage, isFetching, last]
  );

  useEffect(() => {
    fetchMoreOnBottomReached(tableContainerRef.current);
  }, [fetchMoreOnBottomReached]);

  const pendingState = isLoading || isFetching;

  const table = useReactTable({
    data: flatData,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onRowSelectionChange: setRowSelection,
    state: {
      rowSelection,
    },
    getRowId: (row) => row.id,
    enableRowSelection: true,
  });

  const { rows } = table.getRowModel();

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    estimateSize: () => 33, //estimate row height for accurate scrollbar dragging
    getScrollElement: () => tableContainerRef.current,
    //measure dynamic row height, except in firefox because it measures table border height incorrectly
    measureElement:
      typeof window !== "undefined" &&
      navigator.userAgent.indexOf("Firefox") === -1
        ? (element) => element?.getBoundingClientRect().height
        : undefined,
    overscan: 5,
  });

  return (
    <>
      <div className="p-4 bg-white mb-2 rounded">
        <Filters
          submitBtn={submitBtn}
          onSearch={(newFilters) => {
            if (newFilters != filters) {
              setFilters(newFilters);
              setRowSelection({});
            }
          }}
        />
      </div>

      <div className="rounded-sm border border-stroke bg-white shadow-default dark:border-strokedark dark:bg-boxdark">
        <div
          className="overflow-auto"
          onScroll={(e) => fetchMoreOnBottomReached(e.target)}
          ref={tableContainerRef}
          style={{
            overflow: "auto", //our scrollable table container
            position: "relative", //needed for sticky header
            height: "600px", //should be a fixed height
          }}
        >
          <table className="grid w-full">
            <thead className="grid sticky top-0 bg-white border-b z-[10]">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr
                  className="bg-gray-2 text-left dark:bg-meta-4 flex w-full"
                  key={headerGroup.id}
                >
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-4 py-4 flex font-medium text-black dark:text-white"
                      style={{
                        width: header.getSize(),
                      }}
                    >
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody
              style={{
                display: "grid",
                height: `${rowVirtualizer.getTotalSize()}px`, //tells scrollbar how big the table is
                position: "relative", //needed for absolute positioning of rows
              }}
            >
              {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const row = rows[virtualRow.index];
                return (
                  <tr
                    data-index={virtualRow.index} //needed for dynamic row height measurement
                    ref={(node) => rowVirtualizer.measureElement(node)} //measure dynamic row height
                    key={row.id}
                    className={`flex absolute w-full ${
                      row.getIsSelected() ? "bg-yellow-200" : ""
                    }`}
                    style={{
                      transform: `translateY(${virtualRow.start}px)`, //this should always be a `style` as it changes on scroll
                    }}
                    onClick={row.getToggleSelectedHandler()}
                  >
                    {row.getVisibleCells().map((cell) => {
                      return (
                        <td
                          key={cell.id}
                          className="border-b border-r first:border-l border-[#444] flex"
                          style={{
                            width: cell.column.getSize(),
                          }}
                        >
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext()
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="flex justify-center py-5">
          {(isLoading || isFetching || pendingState) && (
            <i className="fas fa-spinner fa-spin text-lg" />
          )}
        </div>
      </div>
    </>
  );
}
