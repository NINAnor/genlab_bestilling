import {
  keepPreviousData,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { config, client } from "../config";
import {
  useReactTable,
  flexRender,
  getCoreRowModel,
  createColumnHelper,
} from "@tanstack/react-table";
import { useEffect, useRef, useCallback, useMemo } from "react";

import { useVirtualizer } from "@tanstack/react-virtual";
import SimpleCellInput from "./Cell/SimpleCellInput";
import DateCell from "./Cell/DateCell";
import SelectCell from "./Cell/SelectCell";
import ActionsCell from "./Cell/ActionsCell";
import MultiSelectCell from "./Cell/MultiSelectCell";

async function getSamples({ pageParam }) {
  const url = pageParam || `/api/samples/?order=${config.order}`;
  const response = await client.get(url);
  return response.data;
}

const columnHelper = createColumnHelper();

const speciesOptions = async (input) => {
  return (await client.get(`/api/species/?order=${config.order}&name__icontains=${input}`)).data;
};

const sampleTypesOptions = async (input) => {
  return (await client.get(`/api/sample-types/?order=${config.order}&name__icontains=${input}`)).data;
};

const markersOptions = async (input) => {
  return (await client.get(`/api/markers/?order=${config.order}&name__icontains=${input}`)).data;
};

const COLUMNS = [
  columnHelper.accessor("guid", {
    header: "GUID",
    cell: SimpleCellInput,
  }),
  columnHelper.accessor("species", {
    header: "Species",
    cell: (props) => <SelectCell {...props} loadOptions={speciesOptions} queryKey={'species'} />,
  }),
  columnHelper.accessor("date", {
    header: "Date",
    cell: DateCell,
  }),
  columnHelper.accessor("pop_id", {
    header: "Pop ID",
    cell: SimpleCellInput,
  }),
  columnHelper.accessor("type", {
    header: "Type",
    cell: (props) => <SelectCell {...props} loadOptions={sampleTypesOptions} queryKey={'sampleTypes'} />,
  }),
  columnHelper.accessor("markers", {
    header: "Markers",
    cell: (props) => <MultiSelectCell {...props} loadOptions={markersOptions} queryKey={'markers'} idField="name" />,
  }),
  columnHelper.accessor("notes", {
    header: "Notes",
    cell: SimpleCellInput,
  }),
  columnHelper.display({
    header: "Actions",
    cell: ActionsCell,
  }),
];

export default function Table() {
  const tableContainerRef = useRef(null);
  const queryClient = useQueryClient();

  const { data, fetchNextPage, isFetching, isLoading } = useInfiniteQuery({
    queryKey: ["samples"],
    queryFn: getSamples,
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
          last.next
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

  const updateCell = useMutation({
    mutationFn: ({ id, ...data }) => {
      return client.patch(`/api/samples/${id}/`, data);
    },
    onSuccess: () => {
      // TODO: feedback
    },
  });

  const deleteRow = useMutation({
    mutationFn: ({ id }) => {
      return client.delete(`/api/samples/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["samples"] });
    },
  });

  const table = useReactTable({
    data: flatData,
    columns: COLUMNS,
    getCoreRowModel: getCoreRowModel(),
    meta: {
      updateData: updateCell.mutateAsync,
      deleteRow: deleteRow.mutateAsync,
    },
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
                    className="flex absolute w-full"
                    style={{
                      transform: `translateY(${virtualRow.start}px)`, //this should always be a `style` as it changes on scroll
                    }}
                  >
                    {row.getVisibleCells().map((cell) => {
                      return (
                        <td
                          key={cell.id}
                          className="border-b border-r first:border-l border-[#333] flex"
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
      </div>
      <div className="mt-4">
        {(isLoading || isFetching) && (
          <p className="font-bold text-center">Loading...</p>
        )}
        {updateCell.isPending && (
          <p className="font-bold text-center">Saving...</p>
        )}
      </div>
    </>
  );
}
