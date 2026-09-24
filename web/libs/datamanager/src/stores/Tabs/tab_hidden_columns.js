import { getRoot, types } from "mobx-state-tree";
import { StringOrNumber } from "../types";

const ColumnsList = types.maybeNull(types.array(StringOrNumber));

export const TabHiddenColumns = types
  .model("TabHiddenColumns", {
    explore: types.optional(ColumnsList, []),
    labeling: types.optional(ColumnsList, []),
  })
  .views((self) => ({
    get length() {
      return self.explore.length + self.labeling.length;
    },

    get activeList() {
      return getRoot(self).isLabeling ? self.labeling : self.explore;
    },

    set activeList(list) {
      if (getRoot(self).isLabeling) {
        // When labeling mode is active, update the labeling hidden columns
        self.labeling = list;
      } else {
        // When not labeling (explore mode), update the explore hidden columns
        self.explore = list;
      }
      // Trigger any MobX reactions that depend on activeList
      this.activeList;
    },

    hasColumn(column) {
      return self.activeList.includes(column.id);
    },
  }))
  .actions((self) => ({
    add(column) {
      const set = new Set(self.activeList);

      set.add(column.id);
      self.activeList = Array.from(set);
    },

    remove(column) {
      const set = new Set(self.activeList);

      set.delete(column.id);
      self.activeList = Array.from(set);
    },
  }))
  .preProcessSnapshot((sn) => {
    return {
      explore: sn?.explore ?? [],
      labeling: sn?.labeling ?? [],
    };
  });
