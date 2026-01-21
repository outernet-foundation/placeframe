#include <DotNet/CesiumForUnity/IonAssetsTreeView.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEditor/IMGUI/Controls/TreeViewState.h>
#include <DotNet/UnityEditor/IMGUI/Controls/TreeView.h>
#include <DotNet/System/Object.h>
#include <DotNet/UnityEditor/IMGUI/Controls/MultiColumnHeader.h>
#include <DotNet/System/String.h>
#include "IonAssetsTreeViewImpl.h"
#include <cstdint>
#include <DotNet/Reinterop/ReinteropException.h>
#include <DotNet/UnityEngine/Rect.h>
#include <DotNet/CesiumForUnity/IonAssetsColumn.h>



namespace DotNet::CesiumForUnity {

IonAssetsTreeView::IonAssetsTreeView(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


IonAssetsTreeView::IonAssetsTreeView(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool IonAssetsTreeView::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool IonAssetsTreeView::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& IonAssetsTreeView::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& IonAssetsTreeView::GetHandle() {
    return this->_handle;
}


void* (*IonAssetsTreeView::Construct_bk3kO2aTAFaE0GWD9sxbig)(void* assetsTreeState, void** reinteropException) = nullptr;


IonAssetsTreeView::IonAssetsTreeView(const ::DotNet::UnityEditor::IMGUI::Controls::TreeViewState& assetsTreeState)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_bk3kO2aTAFaE0GWD9sxbig(assetsTreeState.GetHandle().GetRaw(), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


IonAssetsTreeView::operator ::DotNet::UnityEditor::IMGUI::Controls::TreeView() const {
    return ::DotNet::UnityEditor::IMGUI::Controls::TreeView(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


IonAssetsTreeView::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::IonAssetsTreeView::Property_get_multiColumnHeader)(void* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader IonAssetsTreeView::multiColumnHeader() const {
    void* reinteropException = nullptr;
    auto result = Property_get_multiColumnHeader((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::IonAssetsTreeView::Property_set_multiColumnHeader)(void* thiz, void* value, void** reinteropException) = nullptr;


void IonAssetsTreeView::multiColumnHeader(const ::DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader& value) const {
    void* reinteropException = nullptr;
    Property_set_multiColumnHeader((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*DotNet::CesiumForUnity::IonAssetsTreeView::Property_get_searchString)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::String IonAssetsTreeView::searchString() const {
    void* reinteropException = nullptr;
    auto result = Property_get_searchString((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::IonAssetsTreeView::Property_set_searchString)(void* thiz, void* value, void** reinteropException) = nullptr;


void IonAssetsTreeView::searchString(const ::DotNet::System::String& value) const {
    void* reinteropException = nullptr;
    Property_set_searchString((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::IonAssetsTreeView::CallReload_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


void IonAssetsTreeView::Reload() const {
    void* reinteropException = nullptr;
    CallReload_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void* (*IonAssetsTreeView::Property_get_NativeImplementation)(void*) = nullptr;


::CesiumForUnityNative::IonAssetsTreeViewImpl& IonAssetsTreeView::NativeImplementation() const noexcept {
  return *reinterpret_cast<::CesiumForUnityNative::IonAssetsTreeViewImpl*>(Property_get_NativeImplementation(this->_handle.GetRaw()));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_IonAssetsTreeView_CreateImplementation(void* handle) {
  const ::DotNet::CesiumForUnity::IonAssetsTreeView wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
  auto pImpl = new CesiumForUnityNative::IonAssetsTreeViewImpl(wrapper);
  pImpl->addReference();
  return reinterpret_cast<void*>(pImpl);
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_IonAssetsTreeView_DestroyImplementation(void* pImpl) {
  auto pImplTyped = reinterpret_cast<CesiumForUnityNative::IonAssetsTreeViewImpl*>(pImpl);
  if (pImplTyped) pImplTyped->releaseReference();
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int32_t DotNet_CesiumForUnity_IonAssetsTreeView_GetAssetsCount(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::IonAssetsTreeViewImpl*>(pImpl);const ::DotNet::CesiumForUnity::IonAssetsTreeView wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetAssetsCount(wrapper);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int32_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int32_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int32_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_IonAssetsTreeView_GetAssetName(void* handle, void* pImpl, ::std::int32_t index, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::IonAssetsTreeViewImpl*>(pImpl);const ::DotNet::CesiumForUnity::IonAssetsTreeView wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetAssetName(wrapper, index);
    return result.GetHandle().Release();
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return nullptr;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return nullptr;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return nullptr;
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_IonAssetsTreeView_GetAssetType(void* handle, void* pImpl, ::std::int32_t index, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::IonAssetsTreeViewImpl*>(pImpl);const ::DotNet::CesiumForUnity::IonAssetsTreeView wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetAssetType(wrapper, index);
    return result.GetHandle().Release();
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return nullptr;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return nullptr;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return nullptr;
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int64_t DotNet_CesiumForUnity_IonAssetsTreeView_GetAssetID(void* handle, void* pImpl, ::std::int32_t index, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::IonAssetsTreeViewImpl*>(pImpl);const ::DotNet::CesiumForUnity::IonAssetsTreeView wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetAssetID(wrapper, index);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int64_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int64_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int64_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_IonAssetsTreeView_GetAssetDescription(void* handle, void* pImpl, ::std::int32_t index, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::IonAssetsTreeViewImpl*>(pImpl);const ::DotNet::CesiumForUnity::IonAssetsTreeView wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetAssetDescription(wrapper, index);
    return result.GetHandle().Release();
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return nullptr;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return nullptr;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return nullptr;
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_IonAssetsTreeView_GetAssetAttribution(void* handle, void* pImpl, ::std::int32_t index, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::IonAssetsTreeViewImpl*>(pImpl);const ::DotNet::CesiumForUnity::IonAssetsTreeView wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    auto result = pImplTyped->GetAssetAttribution(wrapper, index);
    return result.GetHandle().Release();
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return nullptr;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return nullptr;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return nullptr;
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_IonAssetsTreeView_CellGUI(void* handle, void* pImpl, const ::DotNet::UnityEngine::Rect* cellRect, ::std::int32_t assetIndex, ::std::uint32_t column, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::IonAssetsTreeViewImpl*>(pImpl);const ::DotNet::CesiumForUnity::IonAssetsTreeView wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->CellGUI(wrapper, *cellRect, assetIndex, ::DotNet::CesiumForUnity::IonAssetsColumn(column));
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_IonAssetsTreeView_Refresh(void* handle, void* pImpl, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::IonAssetsTreeViewImpl*>(pImpl);const ::DotNet::CesiumForUnity::IonAssetsTreeView wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->Refresh(wrapper);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_IonAssetsTreeView_AddAssetToLevel(void* handle, void* pImpl, ::std::int32_t index, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::IonAssetsTreeViewImpl*>(pImpl);const ::DotNet::CesiumForUnity::IonAssetsTreeView wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->AddAssetToLevel(wrapper, index);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_IonAssetsTreeView_AddOverlayToTerrain(void* handle, void* pImpl, ::std::int32_t index, void** reinteropException) {
  try {
    auto pImplTyped = reinterpret_cast<CesiumForUnityNative::IonAssetsTreeViewImpl*>(pImpl);const ::DotNet::CesiumForUnity::IonAssetsTreeView wrapper{::DotNet::Reinterop::ObjectHandle(handle)};
    pImplTyped->AddOverlayToTerrain(wrapper, index);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}

} // extern "C"

