#include <DotNet/UnityEngine/Rendering/SubMeshDescriptor.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/MeshTopology.h>

namespace DotNet::UnityEngine::Rendering {
struct SubMeshDescriptor;
}

namespace DotNet::UnityEngine::Rendering {

void (*SubMeshDescriptor::Construct_hVqvzF5fyHzN08NI0LUuIw)(::std::int32_t indexStart, ::std::int32_t indexCount, ::std::uint32_t topology, ::DotNet::UnityEngine::Rendering::SubMeshDescriptor* pReturnValue, void** reinteropException) = nullptr;


SubMeshDescriptor SubMeshDescriptor::Construct(::std::int32_t indexStart, ::std::int32_t indexCount, ::DotNet::UnityEngine::MeshTopology topology)
{
    void* reinteropException = nullptr;
    SubMeshDescriptor result;
    Construct_hVqvzF5fyHzN08NI0LUuIw(indexStart, indexCount, ::std::uint32_t(topology), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine::Rendering


