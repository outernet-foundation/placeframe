#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::UnityEditor {
class AssemblyReloadCallback;
}

namespace DotNet::UnityEditor {

class AssemblyReloadEvents {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  public: AssemblyReloadEvents() = delete;
  private: static void (*Calladd_afterAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg)(void* value, void** reinteropException);
  public: static void add_afterAssemblyReload(const ::DotNet::UnityEditor::AssemblyReloadCallback& value);
  private: static void (*Callremove_afterAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg)(void* value, void** reinteropException);
  public: static void remove_afterAssemblyReload(const ::DotNet::UnityEditor::AssemblyReloadCallback& value);
  private: static void (*Calladd_beforeAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg)(void* value, void** reinteropException);
  public: static void add_beforeAssemblyReload(const ::DotNet::UnityEditor::AssemblyReloadCallback& value);
  private: static void (*Callremove_beforeAssemblyReload_qCwXhLr_PY2h9aGmfrn7Cg)(void* value, void** reinteropException);
  public: static void remove_beforeAssemblyReload(const ::DotNet::UnityEditor::AssemblyReloadCallback& value);
};

} // namespace DotNet::UnityEditor


